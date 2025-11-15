# BMW iX 2026 Inventory Scraper

A unified scraper for collecting BMW iX 2026 inventory data from multiple dealership platforms.

## Overview

This scraper is specifically designed to find **BMW iX 2026** vehicles from multiple dealership platforms.

Supported dealership platforms:
- **Dealer.com** - Used by BMW of Mountain View, BMW of Fremont, BMW of Berkeley
- **Roadster** - Used by BMW of San Francisco, Peter Pan BMW

**Note:** The scraper is hardcoded to search for BMW iX model year 2026 only. This focus allows for optimized filtering and faster scraping by using URL parameters to pre-filter inventory at the dealership website level.

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Database Setup

The scraper uses SQLite to store vehicle inventory data. The database will be automatically initialized when you run the scraper for the first time.

Database location: `/Users/byte/work/modern-bmws/data/bmw_inventory.db`

Tables:
- `vehicles` - Vehicle inventory data
- `scrape_runs` - Scraping session metadata

## Usage

### Using the convenience wrapper (recommended)

```bash
# Scrape first 5 dealers (default) - searches for iX 2026
./scrape.sh

# Scrape all dealers - searches for iX 2026
./scrape.sh --all

# Scrape first 10 dealers - searches for iX 2026
./scrape.sh --limit 10

# Scrape a specific dealer - searches for iX 2026
./scrape.sh --dealer "BMW of San Francisco"

# Skip database initialization (if already set up)
./scrape.sh --skip-db-init
```

**Note:** All scraping operations automatically filter for BMW iX 2026 models only.

### Using Python directly

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the scraper (automatically searches for iX 2026)
python run_scraper.py --limit 5

# Model and year are hardcoded to iX and 2026
python run_scraper.py --model iX --year 2026 --limit 5
```

## Supported Dealers

Based on the first 5 dealers in `specs/dealers.csv`:

1. **BMW of San Francisco** - https://www.bmwsf.com
   - Platform: Roadster
   - Inventory URL: https://express.bmwsf.com/inventory

2. **BMW of Berkeley** - https://www.weatherfordbmw.com
   - Platform: Dealer.com
   - Inventory URL: https://www.weatherfordbmw.com/new-inventory/index.htm

3. **Peter Pan BMW** - https://www.peterpanbmw.com
   - Platform: Roadster
   - Inventory URL: https://online.peterpanbmw.com/inventory

4. **BMW of Mountain View** - https://www.bmwofmountainview.com
   - Platform: Dealer.com
   - Inventory URL: https://www.bmwofmountainview.com/new-inventory/index.htm

5. **BMW of Fremont** - https://www.bmwoffremont.com
   - Platform: Dealer.com
   - Inventory URL: https://www.bmwoffremont.com/new-inventory/index.htm

## Architecture

### Components

- **run_scraper.py** - Main entry point and orchestrator
  - Reads dealer configurations from CSV
  - Maps dealers to appropriate spiders
  - Initializes database
  - Manages Scrapy CrawlerProcess
  - Handles error logging

- **dealers_scraper/spiders/dealercom_spider.py** - Dealer.com platform spider
  - Uses Playwright for JavaScript rendering
  - Extracts data from `window.DDC.InvData.inventory`
  - Supports pagination

- **dealers_scraper/spiders/roadster_spider.py** - Roadster platform spider
  - Uses Playwright for JavaScript rendering
  - Extracts data from `window.pageData`
  - Vue.js application support

- **dealers_scraper/pipelines.py** - Data processing pipeline
  - VIN-based upsert logic (update if exists, insert if new)
  - Title parsing (year, make, model, trim extraction)
  - Database persistence

- **dealers_scraper/models.py** - SQLAlchemy ORM models
  - Vehicle model with all fields
  - ScrapeRun model for tracking scraping sessions

### Data Flow

```
CSV File → run_scraper.py → Spider Selection → Playwright → Data Extraction → Pipeline → Database
```

## Vehicle Data Schema

Each vehicle record includes:
- `vin` - Vehicle Identification Number (unique)
- `dealer` - Dealership name
- `dealer_platform` - Platform type (Dealer.com, Roadster, etc.)
- `title` - Full vehicle title
- `year` - Model year
- `make` - Manufacturer (typically BMW)
- `model` - Model name (e.g., X3, X5, 3 Series)
- `trim` - Trim level
- `price` - Listed price
- `msrp` - Manufacturer's Suggested Retail Price
- `odometer` - Mileage
- `ext_color` - Exterior color
- `int_color` - Interior color
- `options` - JSON array of option codes
- `source_url` - Source URL where data was scraped
- `scraped_at` - Timestamp of scraping
- `created_at` - First time vehicle was seen
- `updated_at` - Last update timestamp

## Adding New Dealers

To add support for a new dealer:

1. Add the dealer to `specs/dealers.csv`

2. Update the `DEALER_PLATFORM_MAP` in `run_scraper.py`:
```python
DEALER_PLATFORM_MAP = {
    'New Dealer Name': {
        'platform': 'dealercom',  # or 'roadster'
        'inventory_url': 'https://...',
    },
}
```

3. If using a new platform, create a new spider in `dealers_scraper/spiders/`

## Configuration

Scrapy settings are in `dealers_scraper/settings.py`:
- Playwright configuration
- User-Agent settings
- Download delays
- Concurrent request limits
- Pipeline configuration

## Logging

Logs are output to console with timestamps. Log level can be adjusted in `run_scraper.py` or via Scrapy settings.

## Troubleshooting

### Import errors
Make sure you've activated the virtual environment:
```bash
source .venv/bin/activate
```

### Playwright errors
Ensure Playwright browsers are installed:
```bash
playwright install chromium
```

### Database errors
Delete the database and let it re-initialize:
```bash
rm -f ../data/bmw_inventory.db
./scrape.sh
```

### No vehicles found
- Check if the dealer website structure has changed
- Enable debug logging in the spider
- Verify the inventory URL is correct

## Development

### Running individual spiders

```bash
# Run Dealer.com spider for one dealer
scrapy crawl dealercom -a dealer_name="BMW of Mountain View" \
    -a dealer_url="https://www.bmwofmountainview.com/new-inventory/index.htm"

# Run Roadster spider for one dealer
scrapy crawl roadster -a dealer_name="BMW of San Francisco" \
    -a inventory_url="https://express.bmwsf.com/inventory"
```

### Database queries

```bash
# Connect to database
sqlite3 ../data/bmw_inventory.db

# View all vehicles
SELECT dealer, count(*) FROM vehicles GROUP BY dealer;

# View recent scrapes
SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT 10;
```

## License

Internal use only.
