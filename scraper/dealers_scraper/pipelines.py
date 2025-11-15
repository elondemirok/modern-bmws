"""
Item pipelines for dealers_scraper.
Handles database storage with VIN-based upsert logic.
"""
import os
import re
from datetime import datetime

from dealers_scraper.models import Vehicle, get_engine, get_session


class VehiclePipeline:
    """Pipeline to save vehicle data to SQLite database."""

    def __init__(self):
        self.engine = None
        self.session = None

    def open_spider(self, spider):
        """Initialize database connection when spider opens."""
        database_url = os.getenv('DATABASE_URL', 'sqlite:////data/bmw_inventory.db')
        spider.logger.info(f"Connecting to database: {database_url}")
        self.engine = get_engine(database_url)
        self.session = get_session(self.engine)

    def close_spider(self, spider):
        """Close database connection when spider closes."""
        if self.session:
            self.session.close()

    def process_item(self, item, spider):
        """
        Process scraped item and save to database.
        Performs VIN-based upsert: update if exists, insert if new.
        """
        try:
            # Parse title to extract year, make, model, trim
            parsed = self.parse_title(item.get('title', ''))

            # Check if vehicle with this VIN already exists
            existing = self.session.query(Vehicle).filter_by(vin=item['vin']).first()

            now = datetime.utcnow()

            if existing:
                # Update existing vehicle
                spider.logger.info(f"Updating existing vehicle: {item['vin']}")
                existing.dealer = item.get('dealer', existing.dealer)
                existing.title = item.get('title', existing.title)
                existing.year = parsed.get('year', existing.year)
                existing.make = parsed.get('make', existing.make)
                existing.model = parsed.get('model', existing.model)
                existing.trim = parsed.get('trim', existing.trim)
                existing.msrp = item.get('msrp', existing.msrp)
                existing.price = item.get('price', existing.price)
                existing.odometer = item.get('odometer', existing.odometer)
                existing.ext_color = item.get('ext_color', existing.ext_color)
                existing.int_color = item.get('int_color', existing.int_color)
                existing.options = item.get('options', existing.options)
                existing.dealer_platform = item.get('dealer_platform', existing.dealer_platform)
                existing.source_url = item.get('source_url', existing.source_url)
                existing.scraped_at = now
                existing.updated_at = now
            else:
                # Insert new vehicle
                spider.logger.info(f"Inserting new vehicle: {item['vin']}")
                vehicle = Vehicle(
                    dealer=item.get('dealer'),
                    title=item.get('title'),
                    year=parsed.get('year'),
                    make=parsed.get('make', 'BMW'),
                    model=parsed.get('model', 'X3'),
                    trim=parsed.get('trim'),
                    vin=item['vin'],
                    msrp=item.get('msrp'),
                    price=item.get('price'),
                    odometer=item.get('odometer'),
                    ext_color=item.get('ext_color'),
                    int_color=item.get('int_color'),
                    options=item.get('options'),
                    dealer_platform=item.get('dealer_platform'),
                    source_url=item.get('source_url'),
                    scraped_at=now,
                    updated_at=now,
                    created_at=now
                )
                self.session.add(vehicle)

            # Commit the transaction
            self.session.commit()
            spider.logger.info(f"Successfully saved vehicle: {item['vin']}")

        except Exception as e:
            self.session.rollback()
            spider.logger.error(f"Error saving vehicle {item.get('vin', 'UNKNOWN')}: {e}")
            raise

        return item

    def parse_title(self, title):
        """
        Parse vehicle title to extract year, make, model, and trim.
        Example: "2024 BMW X3 xDrive30i" -> {year: 2024, make: 'BMW', model: 'X3', trim: 'xDrive30i'}
        """
        result = {
            'year': None,
            'make': 'BMW',
            'model': 'X3',
            'trim': None
        }

        if not title:
            return result

        # Extract year (4 digits at start)
        year_match = re.search(r'^\s*(\d{4})', title)
        if year_match:
            result['year'] = int(year_match.group(1))

        # Extract make (usually after year)
        make_match = re.search(r'\d{4}\s+(BMW|Mercedes-Benz|Audi|Lexus|[A-Z][a-z]+)', title, re.IGNORECASE)
        if make_match:
            result['make'] = make_match.group(1)

        # Extract model (usually X3, X5, etc.)
        model_match = re.search(r'(X\d|[A-Z]\d+|[A-Z][a-z]+\s+[A-Z]\d+)', title)
        if model_match:
            result['model'] = model_match.group(1)

        # Extract trim (everything after model)
        # Remove year, make, and model from title to get trim
        trim = title
        if year_match:
            trim = trim.replace(year_match.group(0), '', 1)
        if make_match:
            trim = re.sub(r'BMW\s*', '', trim, count=1, flags=re.IGNORECASE)
        if model_match:
            trim = trim.replace(model_match.group(0), '', 1)

        trim = trim.strip()
        if trim:
            result['trim'] = trim

        return result
