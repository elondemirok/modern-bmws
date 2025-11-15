# Valencia BMW Integration Guide

This guide explains how to scrape inventory data from Valencia BMW's website.

## Overview

Valencia BMW is fully configured and supported in this application:
- **Location**: Valencia, CA
- **Website**: https://www.valenciabmw.com
- **Phone**: (661) 775-1500
- **Platform**: Dealer.com
- **Inventory URL**: https://www.valenciabmw.com/new-inventory/index.htm

## Quick Start

### Option 1: Using the Web UI

1. Start the application:
   ```bash
   docker compose up --build
   ```

2. Open your browser to [http://localhost:9292](http://localhost:9292)

3. Open your browser's developer console and run:
   ```javascript
   fetch('/api/scrape', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ dealer: 'Valencia BMW' })
   }).then(r => r.json()).then(console.log)
   ```

4. Wait for the scrape to complete (check logs or API status)

5. Refresh the page to see Valencia BMW inventory

### Option 2: Using the API

```bash
# Start the application
docker compose up --build

# In another terminal, trigger Valencia BMW scrape
curl -X POST http://localhost:9292/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"dealer": "Valencia BMW"}'

# Check scrape status
curl http://localhost:9292/api/status

# View Valencia BMW vehicles
curl "http://localhost:9292/api/vehicles?dealer=Valencia%20BMW"
```

### Option 3: Command Line (Development)

```bash
cd scraper
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Scrape Valencia BMW for iX 2026
python run_scraper.py --dealer "Valencia BMW" --model iX --year 2026

# Scrape all Valencia BMW inventory
python run_scraper.py --dealer "Valencia BMW"
```

## Technical Details

### Platform: Dealer.com

Valencia BMW uses the Dealer.com platform, which means:
- Inventory data is stored in `window.DDC.InvData.inventory.inventory`
- JavaScript rendering is required (handled by Playwright)
- URL filtering is supported via query parameters

### Scraper Configuration

The scraper is pre-configured in `/scraper/run_scraper.py`:

```python
'Valencia BMW': {
    'platform': 'dealercom',
    'inventory_url': 'https://www.valenciabmw.com/new-inventory/index.htm',
}
```

### URL Filtering

When scraping for BMW iX 2026, the scraper automatically constructs:
```
https://www.valenciabmw.com/new-inventory/index.htm?year=2026&model=iX&status=1-1
```

This filters for:
- `year=2026` - 2026 model year
- `model=iX` - BMW iX model
- `status=1-1` - In-stock vehicles only

## Verification

To verify Valencia BMW is properly configured, check:

1. **Platform Map**: Confirm in `/scraper/run_scraper.py` line 147-150
2. **Website Access**: Visit https://www.valenciabmw.com/new-inventory/index.htm
3. **Dealer.com Detection**: Page should load with `window.DDC` object

## Troubleshooting

### No results found

If no vehicles are returned:
1. Check that Valencia BMW has iX 2026 inventory on their website
2. Review scraper logs in `/logs/` directory
3. Try scraping without filters: `--dealer "Valencia BMW"` (no --model)

### Scraper errors

If the scraper fails:
1. Check the log file specified in the API response
2. Verify the website is accessible
3. Ensure Playwright/Chromium is installed correctly
4. Check for bot detection (Dealer.com may block automated requests)

### API timeout

If the API times out:
1. The scraper runs in background - check `/api/status` for progress
2. Monitor logs in `/logs/scraper-*.log`
3. Valencia BMW scraping typically takes 30-60 seconds

## Support

Valencia BMW is one of 28 California BMW dealerships configured in this application. All dealers are listed in `/specs/dealers.csv`.

For issues specific to Valencia BMW scraping, check:
- Spider implementation: `/scraper/dealers_scraper/spiders/dealercom_spider.py`
- Dealer configuration: `/scraper/run_scraper.py` (DEALER_PLATFORM_MAP)
- Test suite: `/tests/test_valencia_bmw.py`
