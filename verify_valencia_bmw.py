#!/usr/bin/env python3
"""
Simple verification script to check Valencia BMW configuration.
"""
import sys
from pathlib import Path

# Add scraper to path
sys.path.insert(0, str(Path(__file__).parent / 'scraper'))

from run_scraper import DEALER_PLATFORM_MAP, DealerConfig
from dealers_scraper.spiders.dealercom_spider import DealercomSpider


def main():
    print("=" * 70)
    print("Valencia BMW Configuration Verification")
    print("=" * 70)
    print()

    # Check 1: Verify dealer in platform map
    print("✓ Checking DEALER_PLATFORM_MAP...")
    if "Valencia BMW" in DEALER_PLATFORM_MAP:
        config = DEALER_PLATFORM_MAP["Valencia BMW"]
        print(f"  ✓ Valencia BMW found in platform map")
        print(f"    Platform: {config['platform']}")
        print(f"    Inventory URL: {config['inventory_url']}")
    else:
        print("  ✗ Valencia BMW NOT found in platform map")
        sys.exit(1)

    print()

    # Check 2: Verify DealerConfig
    print("✓ Checking DealerConfig initialization...")
    dealer_config = DealerConfig(
        name="Valencia BMW",
        city="Valencia",
        website="https://www.valenciabmw.com",
        phone="(661) 775-1500"
    )

    if dealer_config.is_supported():
        print(f"  ✓ Valencia BMW is supported")
        print(f"    Platform: {dealer_config.platform}")
        print(f"    Inventory URL: {dealer_config.inventory_url}")
    else:
        print("  ✗ Valencia BMW is NOT supported")
        sys.exit(1)

    print()

    # Check 3: Verify spider initialization
    print("✓ Checking DealercomSpider initialization...")
    try:
        spider = DealercomSpider(
            dealer_name="Valencia BMW",
            dealer_url="https://www.valenciabmw.com/new-inventory/index.htm",
            model="iX",
            year="2026"
        )
        print(f"  ✓ Spider initialized successfully")
        print(f"    Dealer: {spider.dealer_name}")
        print(f"    Model: {spider.model}")
        print(f"    Year: {spider.year}")
        print(f"    URL: {spider.dealer_url}")

        # Check URL contains filters
        if "year=2026" in spider.dealer_url and "model=iX" in spider.dealer_url:
            print(f"  ✓ URL properly filtered for iX 2026")
        else:
            print(f"  ✗ URL filtering may not be correct")
            sys.exit(1)

    except Exception as e:
        print(f"  ✗ Spider initialization failed: {e}")
        sys.exit(1)

    print()
    print("=" * 70)
    print("✓ All checks passed! Valencia BMW is properly configured.")
    print("=" * 70)
    print()
    print("To scrape Valencia BMW from command line:")
    print("  cd scraper")
    print("  python run_scraper.py --dealer \"Valencia BMW\" --model iX --year 2026")
    print()
    print("To scrape Valencia BMW via API:")
    print("  POST /api/scrape")
    print("  Body: {\"dealer\": \"Valencia BMW\"}")
    print()


if __name__ == '__main__':
    main()
