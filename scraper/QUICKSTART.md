# Quick Start Guide

## Run the Scraper (First 5 Dealers)

```bash
cd /Users/byte/work/modern-bmws/scraper
./scrape.sh
```

This will scrape the first 5 dealers from `specs/dealers.csv`:
- BMW of San Francisco (Roadster platform)
- BMW of Berkeley (Weatherford - **skipped**)
- Peter Pan BMW (Roadster platform)
- BMW of Mountain View (Dealer.com platform)
- BMW of Fremont (Dealer.com platform)

**Note:** BMW of Berkeley uses the Weatherford platform which is not yet supported, so only 4 dealers will actually be scraped.

## Other Usage Examples

```bash
# Scrape a specific dealer
./scrape.sh --dealer "BMW of San Francisco"

# Scrape first 10 dealers
./scrape.sh --limit 10

# Scrape all dealers in CSV
./scrape.sh --all

# Skip database initialization (if already set up)
./scrape.sh --skip-db-init --limit 5
```

## View Results

The scraped data is stored in SQLite database at:
`/Users/byte/work/modern-bmws/data/bmw_inventory.db`

To view results:

```bash
# Use sqlite3
sqlite3 /Users/byte/work/modern-bmws/data/bmw_inventory.db

# Example queries:
sqlite> SELECT dealer, COUNT(*) as count FROM vehicles GROUP BY dealer;
sqlite> SELECT * FROM vehicles LIMIT 10;
sqlite> SELECT vin, dealer, title, price FROM vehicles WHERE model LIKE '%X3%';
```

## Supported Platforms

| Platform | Dealers | Status |
|----------|---------|--------|
| Roadster | BMW of San Francisco, Peter Pan BMW | Supported |
| Dealer.com | BMW of Mountain View, BMW of Fremont | Supported |
| Weatherford | BMW of Berkeley | Not yet supported |

## Troubleshooting

If you encounter any issues:

1. **Make sure virtual environment is set up:**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/playwright install chromium
   ```

2. **Check logs:** The scraper outputs detailed logs to console

3. **Database issues:** Delete and re-initialize:
   ```bash
   rm /Users/byte/work/modern-bmws/data/bmw_inventory.db
   ./scrape.sh
   ```

## What Gets Scraped

For each vehicle, the scraper collects:
- VIN (unique identifier)
- Title, year, make, model, trim
- Price and MSRP
- Exterior/interior colors
- Odometer reading
- Options/packages (when available)
- Source URL

All data is deduplicated by VIN - if a vehicle is scraped multiple times, it will be updated rather than duplicated.
