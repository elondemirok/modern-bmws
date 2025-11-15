#!/bin/bash
# Run scraper sequentially, one dealer at a time

set -e

source venv/bin/activate

export DATABASE_URL="sqlite:///$(pwd)/data/bmw_inventory.db"
export PLAYWRIGHT_HEADLESS=false

echo "🚀 Starting SEQUENTIAL BMW scraper..."
echo "📊 Database: $DATABASE_URL"
echo "🌐 Scraping dealers one at a time for BMW iX 2026"
echo ""

# List of all dealers
dealers=(
    "BMW of San Francisco"
    "BMW of Berkeley"
    "Peter Pan BMW"
    "BMW of Mountain View"
    "BMW of Fremont"
    "BMW Concord"
    "East Bay BMW"
    "Niello BMW"
    "BMW of Elk Grove"
    "Monterey BMW"
    "BMW of Beverly Hills"
    "Century West BMW"
    "New Century BMW"
    "Long Beach BMW"
    "Crevier BMW"
    "BMW of Riverside"
    "BMW of Murrieta"
    "BMW of San Diego"
    "BMW of Encinitas"
    "Shelly BMW"
    "Bob Smith BMW"
    "Rusnak BMW"
    "BMW of Palm Springs"
    "BMW Fresno"
    "BMW of Bakersfield"
    "BMW of Visalia"
)

total=${#dealers[@]}
count=0

for dealer in "${dealers[@]}"; do
    count=$((count + 1))
    echo "[$count/$total] Scraping: $dealer"
    # Run each dealer in a separate Python process to avoid CrawlerProcess restart issues
    # Use --csv with full path to ensure all dealers are loaded
    (cd scraper && python run_scraper.py --dealer "$dealer" --model iX --year 2026 --csv ../specs/dealers.csv) || echo "  ⚠️  Failed to scrape $dealer"
    echo ""
    # Small delay between dealers
    sleep 2
done

echo "✅ Sequential scraping complete! Check the database at data/bmw_inventory.db"
