# aprs_scrape

`aprs_scrape` is a Python-based tool designed to gently scrape station information from [aprs.fi](https://aprs.fi/).

## Features

- Fetches real-time data of APRS stations.
- Parses and stores station information for analysis.
- Designed to minimize load on the aprs.fi servers.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.6 or higher
- Docker (optional, for containerized deployment)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AaronWebster/aprs_scrape.git
   cd aprs_scrape
   ```

2. **Set up a virtual environment (recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Configure the scraper:**

   Ensure you have the necessary permissions to scrape data from aprs.fi. Update any configuration settings in `aprs_scrape.py` as needed.

2. **Run the scraper:**

   ```bash
   python aprs_scrape.py
   ```

   The script will fetch and store station information in the designated output directory.

## Docker Deployment

For containerized deployment:

1. **Build the Docker image:**

   ```bash
   docker build -t aprs_scrape .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -d aprs_scrape
   ```

   This will start the scraper inside a Docker container.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes. Ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](https://github.com/AaronWebster/aprs_scrape/blob/master/LICENSE) file for details.

## Acknowledgements

Special thanks to [aprs.fi](https://aprs.fi/) for providing access to APRS data.

---

*Note: Scraping websites should always be done in accordance with their terms of service. Ensure you have permission to scrape data from aprs.fi and use the tool responsibly to avoid overloading their servers.* 
