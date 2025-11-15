# BMW iX 2026 Finder

A local BMW inventory finder application that searches for BMW iX 2026 vehicles directly from dealership websites and presents them in a clean, filterable web interface.

## Overview

This application is specifically designed to find **BMW iX 2026** vehicles from California BMW dealerships. It features:

- **Automated web scraping** from multiple dealership platforms (Dealer.com, Roadster)
- **Local web UI** for browsing and filtering results
- **Real-time scraping** triggered from the web interface
- **SQLite database** for storing and querying vehicle inventory
- **Docker Compose** setup for easy deployment

## Quick Start

1. **Start the application:**
   ```bash
   docker compose up --build
   ```

2. **Access the web UI:**
   Open your browser to [http://localhost:9292](http://localhost:9292)

3. **Scrape for vehicles:**
   Click the "Scrape Now" button to search for BMW iX 2026 vehicles from configured dealerships

4. **Filter and browse:**
   Use the dealer and price filters to narrow down results

## Features

### Web UI
- Clean, modern interface for browsing BMW iX 2026 inventory
- Real-time scraping triggered from the UI
- Filtering by dealer and price range
- Search functionality across all vehicle fields
- Responsive design for mobile and desktop

### Scraper
- Supports multiple dealership platforms:
  - **Dealer.com** (BMW of Mountain View, BMW of Fremont, BMW of Berkeley)
  - **Roadster** (BMW of San Francisco, Peter Pan BMW)
- URL-based filtering for efficient scraping (uses `submodel:iX` and `year:2026` parameters)
- Playwright-powered JavaScript rendering
- VIN-based deduplication
- Comprehensive logging

### Data Storage
- SQLite database with vehicle and scrape run tracking
- Automatic schema initialization
- VIN-based upsert logic (updates existing, inserts new)
- Historical scrape run data

## Architecture

```
┌─────────────────┐
│   Web UI        │  FastAPI + Jinja2 templates
│   (Port 9292)   │  Filters, search, scrape controls
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite DB     │  Vehicle inventory + scrape runs
│   (Shared Vol)  │  VIN-based deduplication
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Scraper       │  Scrapy + Playwright
│   (Docker)      │  DealercomSpider + RoadsterSpider
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Dealerships   │  BMW of SF, Berkeley, Mountain View,
│   (Websites)    │  Fremont, Peter Pan BMW
└─────────────────┘
```

## Project Structure

```
modern-bmws/
├── docker-compose.yml          # Multi-container setup
├── specs/
│   ├── overview.md             # Requirements and specifications
│   └── dealers.csv             # Dealer list and website info
├── web/                        # FastAPI web application
│   ├── main.py                 # API endpoints and UI routes
│   ├── templates/index.html    # Web UI template
│   ├── static/                 # CSS and JavaScript
│   └── requirements.txt
├── scraper/                    # Scrapy scraper
│   ├── run_scraper.py          # Main entry point
│   ├── dealers_scraper/
│   │   ├── spiders/
│   │   │   ├── dealercom_spider.py
│   │   │   └── roadster_spider.py
│   │   ├── pipelines.py        # Data processing
│   │   └── models.py           # SQLAlchemy ORM
│   └── requirements.txt
├── tests/                      # Test suite
│   ├── test_api.py             # API integration tests (43 tests)
│   └── test_scrapers.py        # Scraper unit tests (50 tests)
└── data/                       # SQLite database (shared volume)
```

## Configuration

### Hardcoded Settings
The application is configured to search exclusively for:
- **Model:** BMW iX
- **Year:** 2026

This focus allows for:
- Faster scraping via URL-based filtering
- Simplified UI (no model selection needed)
- Optimized dealer website queries

### Supported Dealers
The first 5 dealers from `specs/dealers.csv` are used as integration test opportunities:
1. BMW of San Francisco
2. BMW of Berkeley
3. Peter Pan BMW
4. BMW of Mountain View
5. BMW of Fremont

## Development

### Running Tests
```bash
# API tests (43 tests)
pytest tests/test_api.py -v

# Scraper tests (50 tests)
pytest tests/test_scrapers.py -v

# All tests with coverage
pytest tests/ -v --cov=web --cov=scraper/dealers_scraper
```

### Running Linting
```bash
# Check code quality
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Local Development (without Docker)

**Web UI:**
```bash
cd web
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 9292
```

**Scraper:**
```bash
cd scraper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python run_scraper.py --limit 5
```

## API Documentation

### GET /api/vehicles
Get vehicle inventory with optional filters.

**Query Parameters:**
- `dealer` - Filter by dealer name
- `model` - Filter by model
- `min_price` - Minimum price
- `max_price` - Maximum price
- `search` - Text search (title, VIN, colors)
- `limit` - Max results (default: 100)

### POST /api/scrape
Trigger a scrape operation.

**Body (optional):**
```json
{
  "platform": "dealercom"  // or "roadster" or "all"
}
```

Always scrapes for iX 2026 regardless of parameters.

### GET /api/stats
Get inventory statistics and last scrape run info.

### GET /api/status
Get current scraper process status.

### GET /api/dealers
Get list of unique dealers in database.

### GET /api/models
Get list of unique models in database.

## Testing & Validation

### Current Test Coverage
- **API Tests:** 43 passing tests covering all endpoints
- **Scraper Tests:** 50 passing tests for data parsing
- **Linting:** All code passes ruff checks

### Integration Testing
The application uses the first 5 rows of `specs/dealers.csv` as integration test opportunities. These dealers represent different platforms and configurations.

## Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap and progress
- [Specs Overview](specs/overview.md) - Requirements and specifications
- [Scraper README](scraper/README.md) - Scraper architecture and usage
- [Tests README](tests/README.md) - Test suite documentation

## License

Internal use only.
