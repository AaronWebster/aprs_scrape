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

# Use the official Python 3 slim image
FROM python:3-slim

# Install required Debian packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libsqlite3-mod-spatialite \
        sqlite3 \
	procps \
        && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the script and other necessary files to /app
COPY aprs_scrape.py /app

# Install required Python packages
RUN pip install --no-cache-dir requests

# Ensure that mod_spatialite is accessible
ENV SPATIALITE_LIBRARY_PATH="/usr/lib/$(uname -m)-linux-gnu/mod_spatialite.so"

# Set the entrypoint to run the script
CMD ["python3", "-u", "aprs_scrape.py"]


