#!/bin/bash
# Test scraping a single dealer for debugging

source venv/bin/activate

export DATABASE_URL="sqlite:///$(pwd)/data/bmw_inventory.db"
export PLAYWRIGHT_HEADLESS=false

cd scraper

echo "🧪 Testing single dealer: BMW of Mountain View"
echo "📊 Database: $DATABASE_URL"
echo "🌐 URL: https://www.bmwofmountainview.com/new-inventory/index.htm?year=2026&model=iX"
echo ""

python run_scraper.py --dealer "BMW of Mountain View" --model iX --year 2026

echo ""
echo "✅ Test complete!"
