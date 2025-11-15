"""
Pytest configuration and shared fixtures for BMW Dealership Inventory tests.
"""
import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add project directories to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'scraper'))
sys.path.insert(0, str(project_root / 'web'))

# Add Docker container paths if running in Docker
if Path('/scraper').exists():
    sys.path.insert(0, '/scraper')
if Path('/app').exists():
    sys.path.insert(0, '/app')

# Change to web directory for static files (handle both local and Docker paths)
web_dir = project_root / 'web'
if not web_dir.exists() and Path('/app').exists():
    web_dir = Path('/app')
if web_dir.exists():
    os.chdir(web_dir)

from dealers_scraper.models import Base, ScrapeRun, Vehicle  # noqa: E402


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an async test"
    )


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory) -> str:
    """
    Create a temporary database path for testing.

    Returns:
        str: Path to the test database file
    """
    tmp_dir = tmp_path_factory.mktemp("data")
    return str(tmp_dir / "test_bmw_inventory.db")


@pytest.fixture(scope="function")
def db_engine(test_db_path):
    """
    Create a test database engine.

    Args:
        test_db_path: Path to the test database

    Yields:
        Engine: SQLAlchemy engine for testing
    """
    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a test database session.

    Args:
        db_engine: SQLAlchemy engine

    Yields:
        Session: SQLAlchemy session for testing
    """
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_db_engine(db_engine):
    """
    Alias for db_engine fixture for compatibility with existing tests.

    Args:
        db_engine: SQLAlchemy engine

    Returns:
        Engine: SQLAlchemy engine for testing
    """
    return db_engine


@pytest.fixture
def sample_vehicle_data() -> dict:
    """
    Provide sample vehicle data for testing.

    Returns:
        dict: Sample vehicle data
    """
    return {
        "dealer": "Test BMW Dealership",
        "title": "2024 BMW M3 Competition",
        "year": 2024,
        "make": "BMW",
        "model": "M3",
        "trim": "Competition",
        "vin": "WBS8M9C50PCJ12345",
        "msrp": 85000.00,
        "price": 82000.00,
        "odometer": 10,
        "ext_color": "Brooklyn Grey",
        "int_color": "Black",
        "options": '["Premium Package", "Carbon Fiber Trim"]',
        "dealer_platform": "dealeron",
        "source_url": "https://example.com/vehicle/12345",
    }


@pytest.fixture
def sample_vehicle(db_session: Session, sample_vehicle_data: dict) -> Vehicle:
    """
    Create and persist a sample vehicle in the test database.

    Args:
        db_session: Database session
        sample_vehicle_data: Sample vehicle data

    Returns:
        Vehicle: Created vehicle instance
    """
    vehicle = Vehicle(**sample_vehicle_data)
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle


@pytest.fixture
def sample_scrape_run_data() -> dict:
    """
    Provide sample scrape run data for testing.

    Returns:
        dict: Sample scrape run data
    """
    return {
        "platform": "dealeron",
        "status": "completed",
        "vehicles_scraped": 150,
        "dealers_scraped": 5,
        "error_message": None,
    }


@pytest.fixture
def sample_scrape_run(db_session: Session, sample_scrape_run_data: dict) -> ScrapeRun:
    """
    Create and persist a sample scrape run in the test database.

    Args:
        db_session: Database session
        sample_scrape_run_data: Sample scrape run data

    Returns:
        ScrapeRun: Created scrape run instance
    """
    scrape_run = ScrapeRun(**sample_scrape_run_data)
    db_session.add(scrape_run)
    db_session.commit()
    db_session.refresh(scrape_run)
    return scrape_run


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, test_db_path):
    """
    Setup test environment variables and patch the app's database connection.

    Args:
        monkeypatch: Pytest monkeypatch fixture
        test_db_path: Path to test database
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Set environment variable for new processes
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

    # Patch the app's database connection to use test database
    test_engine = create_engine(f"sqlite:///{test_db_path}", echo=False)
    TestSessionLocal = sessionmaker(bind=test_engine)

    # Monkeypatch the main app's database objects
    import main
    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", TestSessionLocal)
