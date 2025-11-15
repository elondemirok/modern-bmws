#!/usr/bin/env python3
"""
Database initialization script for BMW dealership scraper.
Creates the SQLite database and all required tables.
"""
import sys
from pathlib import Path

# Add the scraper directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from dealers_scraper.models import get_session, init_db


def main():
    """Initialize the database."""
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)

    db_path = data_dir / 'bmw_inventory.db'
    database_url = f'sqlite:///{db_path}'

    print(f"Initializing database at: {db_path}")

    # Create database and tables
    engine = init_db(database_url)
    print("✓ Database tables created successfully")

    # Verify connection
    session = get_session(engine)
    print("✓ Database connection verified")
    session.close()

    print(f"\nDatabase ready at: {db_path}")
    print("Tables created: vehicles, scrape_runs")


if __name__ == '__main__':
    main()
