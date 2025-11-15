#!/bin/bash
# Run the BMW scraper locally (non-headless mode - browsers will be visible)

set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup_local.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export DATABASE_URL="sqlite:///$(pwd)/data/bmw_inventory.db"
export PLAYWRIGHT_HEADLESS=false

# Change to scraper directory and run
cd scraper

echo "🚀 Starting BMW scraper (non-headless mode)..."
echo "📊 Database: $DATABASE_URL"
echo "🌐 Scraping all 26 dealers for BMW iX 2026"
echo "🖥️  Chromium windows will appear on your screen"
echo ""

python run_scraper.py --all --model iX --year 2026

echo ""
echo "✅ Scraping complete! Check the database at data/bmw_inventory.db"
