#!/usr/bin/env python3
"""
Unified spider runner for BMW dealership inventory scraping.

This script reads dealer configurations from dealers.csv and runs the appropriate
spider (Dealer.com or Roadster) for each dealer. It handles database initialization,
error handling, and progress logging.

Usage:
    python run_scraper.py                    # Scrape first 5 dealers
    python run_scraper.py --all              # Scrape all dealers
    python run_scraper.py --limit 10         # Scrape first N dealers
    python run_scraper.py --dealer "BMW of San Francisco"  # Scrape specific dealer
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add scraper directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import centralized logging configuration
# Import models for database initialization
from dealers_scraper.models import get_session, init_db

# Import spiders
from dealers_scraper.spiders.dealercom_spider import DealercomSpider
from dealers_scraper.spiders.roadster_spider import RoadsterSpider
from logging_config import setup_logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Configure logging using centralized configuration
logger = setup_logging('scraper')


# Dealer platform mapping based on known configurations
DEALER_PLATFORM_MAP = {
    'BMW of San Francisco': {
        'platform': 'roadster',
        'inventory_url': 'https://express.bmwsf.com/inventory',
    },
    'BMW of Berkeley': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.weatherfordbmw.com/new-inventory/index.htm',
    },
    'Peter Pan BMW': {
        'platform': 'roadster',
        'inventory_url': 'https://online.peterpanbmw.com/inventory',
    },
    'BMW of Mountain View': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofmountainview.com/new-inventory/index.htm',
    },
    'BMW of Fremont': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwoffremont.com/new-inventory/index.htm',
    },
    'BMW Concord': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwconcord.com/new-inventory/index.htm',
    },
    'East Bay BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.eastbaybmw.com/new-inventory/index.htm',
    },
    'Niello BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.niellobmw.com/new-inventory/index.htm',
    },
    'BMW of Elk Grove': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofelkgrove.com/new-inventory/index.htm',
    },
    'Monterey BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.montereybmw.com/new-inventory/index.htm',
    },
    'BMW of Beverly Hills': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofbeverlyhills.com/new-inventory/index.htm',
    },
    'Century West BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.centurywestbmw.com/new-inventory/index.htm',
    },
    'New Century BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.newcenturybmw.com/new-inventory/index.htm',
    },
    'Long Beach BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.longbeachbmw.com/new-inventory/index.htm',
    },
    'Crevier BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.crevierbmw.com/new-inventory/index.htm',
    },
    'BMW of Riverside': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwriverside.com/new-inventory/index.htm',
    },
    'BMW of Murrieta': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofmurrieta.com/new-inventory/index.htm',
    },
    'BMW of San Diego': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofsandiego.com/new-inventory/index.htm',
    },
    'BMW of Encinitas': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwencinitas.com/new-inventory/index.htm',
    },
    'Shelly BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.shellybmw.com/new-inventory/index.htm',
    },
    'Bob Smith BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bobsmithbmw.com/new-inventory/index.htm',
    },
    'Rusnak BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.rusnakbmw.com/new-inventory/index.htm',
    },
    'BMW of Palm Springs': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofpalmsprings.com/new-inventory/index.htm',
    },
    'BMW Fresno': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwfresno.com/new-inventory/index.htm',
    },
    'BMW of Bakersfield': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofbakersfield.com/new-inventory/index.htm',
    },
    'BMW of Visalia': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.bmwofvisalia.com/new-inventory/index.htm',
    },
    'Valencia BMW': {
        'platform': 'dealercom',
        'inventory_url': 'https://www.valenciabmw.com/new-inventory/index.htm',
    },
}


class DealerConfig:
    """Dealer configuration container."""

    def __init__(self, name: str, city: str, website: str, phone: str):
        self.name = name
        self.city = city
        self.website = website
        self.phone = phone
        self.platform = None
        self.inventory_url = None

        # Look up platform and inventory URL from mapping
        if name in DEALER_PLATFORM_MAP:
            config = DEALER_PLATFORM_MAP[name]
            self.platform = config['platform']
            self.inventory_url = config['inventory_url']

    def is_supported(self) -> bool:
        """Check if this dealer's platform is supported."""
        return self.platform in ['roadster', 'dealercom'] and self.inventory_url is not None

    def __repr__(self):
        return f"DealerConfig(name='{self.name}', platform='{self.platform}')"


def read_dealers_csv(csv_path: Path, limit: int | None = None) -> list[DealerConfig]:
    """
    Read dealer configurations from CSV file.

    Args:
        csv_path: Path to dealers.csv file
        limit: Maximum number of dealers to read (None for all)

    Returns:
        List of DealerConfig objects
    """
    dealers = []

    try:
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                dealer = DealerConfig(
                    name=row['Dealer'],
                    city=row['City'],
                    website=row['Website'],
                    phone=row['Phone']
                )
                dealers.append(dealer)

        logger.info(f"Read {len(dealers)} dealers from {csv_path}")
        return dealers

    except Exception as e:
        logger.error(f"Error reading dealers CSV: {e}")
        sys.exit(1)


def filter_supported_dealers(dealers: list[DealerConfig]) -> list[DealerConfig]:
    """
    Filter dealers to only include those with supported platforms.

    Args:
        dealers: List of all dealers

    Returns:
        List of dealers with supported platforms
    """
    supported = [d for d in dealers if d.is_supported()]
    unsupported = [d for d in dealers if not d.is_supported()]

    logger.info(f"Dealer filtering results: {len(supported)} supported, {len(unsupported)} unsupported")
    logger.info(f"Supported dealers: {len(supported)}")
    for dealer in supported:
        logger.info(
            f"  - {dealer.name} ({dealer.platform})",
            extra={'dealer_name': dealer.name, 'platform': dealer.platform, 'city': dealer.city}
        )

    if unsupported:
        logger.warning(f"Unsupported/skipped dealers: {len(unsupported)}")
        for dealer in unsupported:
            logger.warning(
                f"  - {dealer.name} ({dealer.platform or 'unknown platform'})",
                extra={'dealer_name': dealer.name, 'platform': dealer.platform, 'city': dealer.city}
            )

    return supported


def initialize_database() -> None:
    """Initialize the SQLite database."""
    try:
        # Ensure data directory exists
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)

        db_path = data_dir / 'bmw_inventory.db'
        database_url = f'sqlite:///{db_path}'

        logger.info(f"Initializing database at: {db_path}")

        # Create database and tables
        engine = init_db(database_url)
        logger.info("Database tables created/verified successfully")

        # Verify connection
        session = get_session(engine)
        session.close()
        logger.info("Database connection verified")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)


def run_scraper(dealers: list[DealerConfig], model: str = None, year: str = None) -> None:
    """
    Run the scraper for all configured dealers.

    Args:
        dealers: List of dealer configurations to scrape
        model: Optional BMW model to filter (e.g., 'iX', '3 Series')
        year: Optional year to filter (defaults to '2026' if model provided)
    """
    if not dealers:
        logger.warning("No dealers to scrape")
        return

    # Get Scrapy settings
    settings = get_project_settings()

    # Configure Scrapy logging
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    scrapy_log_file = logs_dir / f'scrapy-{timestamp}.log'

    settings.set('LOG_FILE', str(scrapy_log_file))
    settings.set('LOG_LEVEL', 'INFO')
    settings.set('LOG_FORMAT', '%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
    settings.set('LOG_DATEFORMAT', '%Y-%m-%d %H:%M:%S')

    logger.info(f"Scrapy logs will be written to: {scrapy_log_file}")

    # Override database URL to use absolute path
    data_dir = Path(__file__).parent.parent / 'data'
    db_path = data_dir / 'bmw_inventory.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

    # Create crawler process
    process = CrawlerProcess(settings)

    # Track scrape run statistics
    total_dealers = len(dealers)
    roadster_count = sum(1 for d in dealers if d.platform == 'roadster')
    dealercom_count = sum(1 for d in dealers if d.platform == 'dealercom')

    logger.info(f"Starting scrape run for {total_dealers} dealers:")
    logger.info(f"  - Roadster platform: {roadster_count} dealers")
    logger.info(f"  - Dealer.com platform: {dealercom_count} dealers")
    if model:
        logger.info(f"  - Filtering for model: {model}, year: {year or '2026'}")

    # Add each dealer's spider to the crawler process
    for dealer in dealers:
        try:
            if dealer.platform == 'roadster':
                logger.info(f"Adding RoadsterSpider for {dealer.name}")
                process.crawl(
                    RoadsterSpider,
                    dealer_name=dealer.name,
                    inventory_url=dealer.inventory_url,
                    model=model,
                    year=year
                )

            elif dealer.platform == 'dealercom':
                logger.info(f"Adding DealercomSpider for {dealer.name}")
                process.crawl(
                    DealercomSpider,
                    dealer_name=dealer.name,
                    dealer_url=dealer.inventory_url,
                    site_id=None,  # Can be extracted from URL if needed
                    model=model,
                    year=year
                )

            else:
                logger.warning(f"Unknown platform '{dealer.platform}' for {dealer.name}")

        except Exception as e:
            logger.error(f"Error adding spider for {dealer.name}: {e}")
            continue

    # Start the crawling process
    logger.info("Starting crawler process...")
    try:
        process.start()
        logger.info("Scraping completed successfully!")

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point for the scraper runner."""
    parser = argparse.ArgumentParser(
        description='Run BMW dealership inventory scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py                          # Scrape first 5 dealers
  python run_scraper.py --all                    # Scrape all dealers
  python run_scraper.py --limit 10               # Scrape first 10 dealers
  python run_scraper.py --dealer "BMW of San Francisco"  # Scrape specific dealer
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Scrape all dealers in CSV file'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Maximum number of dealers to scrape (default: 5)'
    )

    parser.add_argument(
        '--dealer',
        type=str,
        help='Scrape specific dealer by name'
    )

    parser.add_argument(
        '--csv',
        type=Path,
        default=Path(__file__).parent.parent / 'specs' / 'dealers.csv',
        help='Path to dealers CSV file'
    )

    parser.add_argument(
        '--skip-db-init',
        action='store_true',
        help='Skip database initialization (use if already initialized)'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='Filter for specific BMW model (e.g., "iX", "3 Series")'
    )

    parser.add_argument(
        '--year',
        type=str,
        default='2026',
        help='Filter for specific year (default: 2026)'
    )

    args = parser.parse_args()

    # Log execution context
    logger.info("=" * 70)
    logger.info("BMW Dealership Inventory Scraper")
    logger.info("=" * 70)

    # Detect subprocess execution context
    parent_pid = os.getppid()
    current_pid = os.getpid()
    is_subprocess = parent_pid != 1 and 'python' in str(sys.argv[0])

    logger.info(
        f"Execution context - PID: {current_pid}, Parent PID: {parent_pid}",
        extra={
            'process_id': current_pid,
            'parent_process_id': parent_pid,
            'is_subprocess': is_subprocess
        }
    )

    if is_subprocess:
        logger.info("Running as subprocess (likely triggered from web interface)")
    else:
        logger.info("Running from command-line interface")

    # Log command-line arguments
    logger.info("Command-line arguments received:")
    logger.info(f"  --all: {args.all}")
    logger.info(f"  --limit: {args.limit}")
    logger.info(f"  --dealer: {args.dealer}")
    logger.info(f"  --csv: {args.csv}")
    logger.info(f"  --skip-db-init: {args.skip_db_init}")
    logger.info(f"  --model: {args.model}")
    logger.info(f"  --year: {args.year}")
    logger.info(
        "Arguments summary",
        extra={
            'all_dealers': args.all,
            'limit': args.limit,
            'dealer': args.dealer,
            'csv_path': str(args.csv),
            'skip_db_init': args.skip_db_init,
            'model_filter': args.model,
            'year_filter': args.year
        }
    )

    # Initialize database unless skipped
    if not args.skip_db_init:
        initialize_database()
    else:
        logger.info("Skipping database initialization")

    # Read dealers from CSV
    limit = None if args.all else args.limit
    dealers = read_dealers_csv(args.csv, limit=limit)

    # Filter to specific dealer if requested
    if args.dealer:
        dealers = [d for d in dealers if d.name == args.dealer]
        if not dealers:
            logger.error(f"Dealer '{args.dealer}' not found in CSV")
            sys.exit(1)

    # Filter to supported dealers
    supported_dealers = filter_supported_dealers(dealers)

    if not supported_dealers:
        logger.error("No supported dealers found to scrape")
        sys.exit(1)

    # Run the scraper with optional model/year filters
    run_scraper(supported_dealers, model=args.model, year=args.year if args.model else None)

    logger.info("=" * 70)
    logger.info("Scraping session complete!")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
