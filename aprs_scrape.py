#!/usr/bin/env python3
#
# Copyright 2025 HALDO Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import datetime
import json
import sqlite3
import os
import time
import random


def GetRequiredEnv(name, value_type=str):
  """
    Asserts that a required environment variable exists, validates its type, and returns its value.

    Args:
        name (str): The name of the environment variable.
        value_type (type): The expected type of the environment variable's value.
                           Supported types: str, int, float, list.

    Returns:
        The value of the environment variable, converted to the specified type.

    Raises:
        KeyError: If the environment variable is not set.
        ValueError: If the environment variable cannot be converted to the specified type.
    """
  value = os.getenv(name)
  if value is None:
    raise KeyError(f"Required environment variable '{name}' not set.")

  try:
    if value_type == list:
      return value.split(',')
    elif value_type == int:
      return int(value)
    elif value_type == float:
      return float(value)
    elif value_type == str:
      return value
    else:
      raise ValueError(f"Unsupported value type: {value_type}")
  except Exception as e:
    raise ValueError(
        f"Error converting environment variable '{name}' to {value_type}: {e}")


STATIONS = GetRequiredEnv('STATIONS', list)
DATABASE_PATH = GetRequiredEnv('DATABASE_PATH', str)
API_KEY = GetRequiredEnv('API_KEY', str)
MIN_INTERVAL_SEC = GetRequiredEnv('MIN_INTERVAL_SEC', int)
MAX_INTERVAL_SEC = GetRequiredEnv('MAX_INTERVAL_SEC', int)


def FetchStationData():
  """
  Fetch station data from aprs.fi and store in SQLite database.
  Returns True if we successfully retrieved data for at least one station.
  Returns False otherwise (no data or an error occurred).
  """

  station_names = STATIONS
  if not station_names:
    return False

  print(f'Loaded {len(station_names)} stations:')
  for station_name in station_names:
    print(f'  {station_name}')

  BASE_URL = 'https://api.aprs.fi/api/get'
  HEADERS = {
      'User-Agent': 'synapticon/1.0.0-stable (+http://synapticon.uoregon.edu/)'
  }

  # Connect to database
  try:
    sqlite_conn = sqlite3.connect(DATABASE_PATH)
    # Enable extension loading
    sqlite_conn.enable_load_extension(True)
    if os.name == 'nt':
      sqlite_conn.load_extension('mod_spatialite')
    else:
      sqlite_conn.load_extension('mod_spatialite.so')
    sqlite_cur = sqlite_conn.cursor()
  except Exception as e:
    print(f"Error connecting to database {DATABASE_PATH}: {e}")
    return False

  # Create table if it doesn't exist
  create_table_sql = """
        CREATE TABLE IF NOT EXISTS station_table (
            class TEXT,
            name TEXT,
            type TEXT,
            time TEXT,
            lasttime TEXT,
            altitude REAL,  -- in meters
            course INTEGER, -- in degrees
            speed REAL,     -- in km/h
            symbol TEXT,
            srccall TEXT,
            dstcall TEXT,
            path TEXT,
            station_name TEXT,
            location geometry,
            last_beaconed_heading REAL,
            last_beaconed_time TEXT
        );
    """
  sqlite_cur.execute(create_table_sql)

  # We chunk the station_names list into slices of size 20
  batch_size = 20
  any_data_inserted = False

  for i in range(0, len(station_names), batch_size):
    # Take a slice of up to 20 station names
    chunk = station_names[i:i + batch_size]
    station_list_str = ",".join(chunk)

    params = {
        'name': station_list_str,
        'what': 'loc',
        'apikey': API_KEY,
        'format': 'json'
    }

    try:
      response = requests.get(url=BASE_URL, headers=HEADERS, params=params)
      data = response.json()
    except Exception as e:
      print(f"Error fetching data from aprs.fi: {e}")
      sqlite_cur.close()
      sqlite_conn.close()
      return False

    entries = data.get('entries', [])
    if not entries:
      print(f"No data returned for chunk: {chunk}")
      continue

    for entry in entries:
      # lat/lng in decimal degrees
      lng = entry.pop('lng')
      lat = entry.pop('lat')
      entry['location'] = f'POINT({lng} {lat})'

      # Timestamps to ISO
      entry['time'] = datetime.datetime.fromtimestamp(int(
          entry['time'])).isoformat()
      entry['lasttime'] = datetime.datetime.fromtimestamp(int(
          entry['lasttime'])).isoformat()

      # Convert to float
      entry['altitude'] = float(entry['altitude'])  # meters
      entry['course'] = float(entry['course'])  # degrees
      entry['speed'] = float(entry['speed'])  # km/h

      # Station name
      entry['station_name'] = entry['name']

    # Insert/update each entry in the DB
    for entry in entries:
      # Check for existing record with same lasttime and station_name
      sqlite_cur.execute(
          """
                SELECT 1
                FROM station_table
                WHERE lasttime = ? AND station_name = ?
                LIMIT 1
                """, (entry['lasttime'], entry['station_name']))
      if sqlite_cur.fetchone():
        print(
            f"An entry with lasttime {entry['lasttime']} "
            f"and station_name {entry['station_name']} already exists. Skipping..."
        )
        continue

      print('Inserting:', entry)
      insert_sql = """
                INSERT INTO station_table (
                    class, name, type, time, lasttime, altitude,
                    course, speed, symbol, srccall, dstcall, path,
                    station_name, location
                ) VALUES (
                    :class, :name, :type, :time, :lasttime, :altitude,
                    :course, :speed, :symbol, :srccall, :dstcall, :path,
                    :station_name, GeomFromText(:location, 4326)
                )
            """
      sqlite_cur.execute(insert_sql, entry)

      # For brand-new row, set last_beaconed_heading/time the first time
      new_row_id = sqlite_cur.lastrowid
      update_sql = """
                UPDATE station_table
                SET last_beaconed_heading = :course,
                    last_beaconed_time = :lasttime
                WHERE rowid = :rowid
            """
      sqlite_cur.execute(
          update_sql, {
              'course': entry['course'],
              'lasttime': entry['lasttime'],
              'rowid': new_row_id
          })
      any_data_inserted = True

  sqlite_conn.commit()
  sqlite_cur.close()
  sqlite_conn.close()

  return any_data_inserted


def Main():
  print('APRS scraper started.')

  assert MIN_INTERVAL_SEC > 0
  assert MAX_INTERVAL_SEC > 0
  assert MIN_INTERVAL_SEC < MAX_INTERVAL_SEC

  # Start at the minimum interval
  sleep_time_sec = MIN_INTERVAL_SEC

  while True:
    success = FetchStationData()

    if success:
      sleep_time_sec = MIN_INTERVAL_SEC
    else:
      sleep_time_sec = min(sleep_time_sec * 2, MAX_INTERVAL_SEC)

    print(f'Sleeping for {sleep_time_sec} seconds...')
    time.sleep(sleep_time_sec)

    random_delay_sec = random.uniform(0, 5)
    time.sleep(random_delay_sec)


if __name__ == '__main__':
  Main()
