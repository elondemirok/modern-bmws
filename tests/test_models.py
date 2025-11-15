"""
Comprehensive unit tests for database models.

Tests cover:
- Vehicle model creation and validation
- VIN-based upsert logic
- Required fields validation
- ScrapeRun model creation
- Database session operations
- Edge cases
"""
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Add scraper directory to path
scraper_path = Path(__file__).parent.parent / 'scraper'
sys.path.insert(0, str(scraper_path))

from dealers_scraper.models import (  # noqa: E402
    Base,
    ScrapeRun,
    Vehicle,
    get_engine,
    get_session,
    init_db,
)


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine for testing."""
    test_engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session(engine):
    """Create a new database session for testing."""
    Session = sessionmaker(bind=engine)
    test_session = Session()
    yield test_session
    test_session.close()


@pytest.fixture
def sample_vehicle_data():
    """Provide sample vehicle data for tests."""
    return {
        'dealer': 'BMW of Manhattan',
        'title': '2024 BMW M4 Competition Coupe',
        'year': 2024,
        'make': 'BMW',
        'model': 'M4',
        'trim': 'Competition Coupe',
        'vin': '1234567890ABCDEFG',
        'msrp': 89000.00,
        'price': 85000.00,
        'odometer': 0,
        'ext_color': 'Isle of Man Green',
        'int_color': 'Black Merino Leather',
        'options': '["ZCW", "494", "776"]',
        'dealer_platform': 'bmw_ota',
        'source_url': 'https://example.com/vehicle/1234567890ABCDEFG',
    }


class TestVehicleModel:
    """Test cases for the Vehicle model."""

    def test_vehicle_creation(self, session, sample_vehicle_data):
        """Test basic vehicle creation with all fields."""
        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        # Verify vehicle was created
        assert vehicle.id is not None
        assert vehicle.vin == '1234567890ABCDEFG'
        assert vehicle.dealer == 'BMW of Manhattan'
        assert vehicle.title == '2024 BMW M4 Competition Coupe'
        assert vehicle.year == 2024
        assert vehicle.make == 'BMW'
        assert vehicle.model == 'M4'
        assert vehicle.trim == 'Competition Coupe'
        assert vehicle.msrp == 89000.00
        assert vehicle.price == 85000.00
        assert vehicle.odometer == 0
        assert vehicle.ext_color == 'Isle of Man Green'
        assert vehicle.int_color == 'Black Merino Leather'
        assert vehicle.options == '["ZCW", "494", "776"]'
        assert vehicle.dealer_platform == 'bmw_ota'
        assert vehicle.source_url == 'https://example.com/vehicle/1234567890ABCDEFG'

        # Verify timestamps
        assert vehicle.scraped_at is not None
        assert vehicle.updated_at is not None
        assert vehicle.created_at is not None

    def test_vehicle_required_fields(self, session):
        """Test that required fields are enforced."""
        # Missing dealer
        vehicle = Vehicle(
            title='2024 BMW M4',
            make='BMW',
            model='M4',
            vin='1234567890ABCDEFG',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Missing title
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            make='BMW',
            model='M4',
            vin='1234567890ABCDEFH',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Missing make
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            title='2024 BMW M4',
            model='M4',
            vin='1234567890ABCDEFI',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Missing model
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            title='2024 BMW M4',
            make='BMW',
            vin='1234567890ABCDEFJ',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Missing VIN
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            title='2024 BMW M4',
            make='BMW',
            model='M4',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Missing dealer_platform
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            title='2024 BMW M4',
            make='BMW',
            model='M4',
            vin='1234567890ABCDEFK',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Missing source_url
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            title='2024 BMW M4',
            make='BMW',
            model='M4',
            vin='1234567890ABCDEFL',
            dealer_platform='bmw_ota'
        )
        session.add(vehicle)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_vehicle_unique_vin(self, session, sample_vehicle_data):
        """Test that VIN must be unique."""
        # Create first vehicle
        vehicle1 = Vehicle(**sample_vehicle_data)
        session.add(vehicle1)
        session.commit()

        # Try to create second vehicle with same VIN
        vehicle2_data = sample_vehicle_data.copy()
        vehicle2_data['dealer'] = 'BMW of Brooklyn'
        vehicle2 = Vehicle(**vehicle2_data)
        session.add(vehicle2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_vehicle_vin_based_upsert(self, session, sample_vehicle_data):
        """Test VIN-based upsert logic (updating existing vehicles)."""
        # Create initial vehicle
        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()
        initial_id = vehicle.id
        initial_created_at = vehicle.created_at
        initial_updated_at = vehicle.updated_at

        # Query by VIN
        existing_vehicle = session.query(Vehicle).filter_by(vin='1234567890ABCDEFG').first()
        assert existing_vehicle is not None
        assert existing_vehicle.id == initial_id
        assert existing_vehicle.price == 85000.00

        # Update the vehicle (simulating upsert)
        existing_vehicle.price = 82000.00
        existing_vehicle.odometer = 100
        existing_vehicle.scraped_at = datetime.utcnow()
        session.commit()

        # Verify update
        updated_vehicle = session.query(Vehicle).filter_by(vin='1234567890ABCDEFG').first()
        assert updated_vehicle.id == initial_id  # Same ID
        assert updated_vehicle.price == 82000.00  # Updated price
        assert updated_vehicle.odometer == 100  # Updated odometer
        assert updated_vehicle.created_at == initial_created_at  # Created at unchanged
        assert updated_vehicle.updated_at > initial_updated_at  # Updated at changed

    def test_vehicle_price_updates(self, session, sample_vehicle_data):
        """Test updating vehicle prices over time."""
        # Create vehicle with initial price
        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.price == 85000.00

        # Update price (price drop)
        vehicle.price = 83000.00
        session.commit()

        updated_vehicle = session.query(Vehicle).filter_by(vin='1234567890ABCDEFG').first()
        assert updated_vehicle.price == 83000.00

        # Update price again (further price drop)
        updated_vehicle.price = 80000.00
        session.commit()

        final_vehicle = session.query(Vehicle).filter_by(vin='1234567890ABCDEFG').first()
        assert final_vehicle.price == 80000.00

    def test_vehicle_optional_fields(self, session):
        """Test vehicle creation with only required fields (optional fields can be None)."""
        vehicle = Vehicle(
            dealer='BMW of Manhattan',
            title='2024 BMW M4',
            make='BMW',
            model='M4',
            vin='1234567890ABCDEFG',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.year is None
        assert vehicle.trim is None
        assert vehicle.msrp is None
        assert vehicle.price is None
        assert vehicle.odometer is None
        assert vehicle.ext_color is None
        assert vehicle.int_color is None
        assert vehicle.options is None

    def test_vehicle_repr(self, session, sample_vehicle_data):
        """Test Vehicle __repr__ method."""
        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        repr_str = repr(vehicle)
        assert "1234567890ABCDEFG" in repr_str
        assert "BMW of Manhattan" in repr_str
        assert "2024 BMW M4 Competition Coupe" in repr_str

    def test_multiple_vehicles_same_dealer(self, session, sample_vehicle_data):
        """Test creating multiple vehicles from the same dealer."""
        # Create first vehicle
        vehicle1 = Vehicle(**sample_vehicle_data)
        session.add(vehicle1)

        # Create second vehicle with different VIN
        vehicle2_data = sample_vehicle_data.copy()
        vehicle2_data['vin'] = 'DIFFERENT1234VIN99'
        vehicle2_data['title'] = '2024 BMW X5 M'
        vehicle2_data['model'] = 'X5'
        vehicle2 = Vehicle(**vehicle2_data)
        session.add(vehicle2)

        session.commit()

        # Verify both vehicles exist
        vehicles = session.query(Vehicle).filter_by(dealer='BMW of Manhattan').all()
        assert len(vehicles) == 2
        assert set([v.vin for v in vehicles]) == {'1234567890ABCDEFG', 'DIFFERENT1234VIN99'}

    def test_vehicle_query_by_model(self, session, sample_vehicle_data):
        """Test querying vehicles by model."""
        # Create M4
        vehicle1 = Vehicle(**sample_vehicle_data)
        session.add(vehicle1)

        # Create X5
        vehicle2_data = sample_vehicle_data.copy()
        vehicle2_data['vin'] = 'DIFFERENT1234VIN99'
        vehicle2_data['title'] = '2024 BMW X5 M'
        vehicle2_data['model'] = 'X5'
        vehicle2 = Vehicle(**vehicle2_data)
        session.add(vehicle2)

        session.commit()

        # Query M4 models
        m4_vehicles = session.query(Vehicle).filter_by(model='M4').all()
        assert len(m4_vehicles) == 1
        assert m4_vehicles[0].vin == '1234567890ABCDEFG'

        # Query X5 models
        x5_vehicles = session.query(Vehicle).filter_by(model='X5').all()
        assert len(x5_vehicles) == 1
        assert x5_vehicles[0].vin == 'DIFFERENT1234VIN99'

    def test_vehicle_query_by_price_range(self, session, sample_vehicle_data):
        """Test querying vehicles by price range."""
        # Create expensive vehicle
        vehicle1 = Vehicle(**sample_vehicle_data)
        session.add(vehicle1)

        # Create cheaper vehicle
        vehicle2_data = sample_vehicle_data.copy()
        vehicle2_data['vin'] = 'CHEAPER123VIN9999'
        vehicle2_data['price'] = 45000.00
        vehicle2_data['title'] = '2024 BMW 330i'
        vehicle2_data['model'] = '3 Series'
        vehicle2 = Vehicle(**vehicle2_data)
        session.add(vehicle2)

        session.commit()

        # Query vehicles under $50k
        affordable = session.query(Vehicle).filter(Vehicle.price < 50000).all()
        assert len(affordable) == 1
        assert affordable[0].vin == 'CHEAPER123VIN9999'

        # Query vehicles over $80k
        luxury = session.query(Vehicle).filter(Vehicle.price > 80000).all()
        assert len(luxury) == 1
        assert luxury[0].vin == '1234567890ABCDEFG'


class TestScrapeRunModel:
    """Test cases for the ScrapeRun model."""

    def test_scrape_run_creation(self, session):
        """Test basic scrape run creation."""
        scrape_run = ScrapeRun(
            platform='bmw_ota',
            status='running',
            vehicles_scraped=0,
            dealers_scraped=0
        )
        session.add(scrape_run)
        session.commit()

        assert scrape_run.id is not None
        assert scrape_run.platform == 'bmw_ota'
        assert scrape_run.status == 'running'
        assert scrape_run.vehicles_scraped == 0
        assert scrape_run.dealers_scraped == 0
        assert scrape_run.error_message is None
        assert scrape_run.started_at is not None
        assert scrape_run.completed_at is None
        assert scrape_run.pid is None  # PID should be None until process is spawned

    def test_scrape_run_default_status(self, session):
        """Test that default status is 'running'."""
        scrape_run = ScrapeRun(platform='bmw_ota')
        session.add(scrape_run)
        session.commit()

        assert scrape_run.status == 'running'
        assert scrape_run.vehicles_scraped == 0
        assert scrape_run.dealers_scraped == 0

    def test_scrape_run_completion(self, session):
        """Test completing a scrape run."""
        scrape_run = ScrapeRun(platform='bmw_ota')
        session.add(scrape_run)
        session.commit()

        # Update scrape run to completed
        scrape_run.status = 'completed'
        scrape_run.vehicles_scraped = 150
        scrape_run.dealers_scraped = 5
        scrape_run.completed_at = datetime.utcnow()
        session.commit()

        completed_run = session.query(ScrapeRun).filter_by(id=scrape_run.id).first()
        assert completed_run.status == 'completed'
        assert completed_run.vehicles_scraped == 150
        assert completed_run.dealers_scraped == 5
        assert completed_run.completed_at is not None

    def test_scrape_run_failure(self, session):
        """Test marking a scrape run as failed with error message."""
        scrape_run = ScrapeRun(platform='bmw_ota')
        session.add(scrape_run)
        session.commit()

        # Mark as failed
        scrape_run.status = 'failed'
        scrape_run.error_message = 'Connection timeout to dealer website'
        scrape_run.completed_at = datetime.utcnow()
        session.commit()

        failed_run = session.query(ScrapeRun).filter_by(id=scrape_run.id).first()
        assert failed_run.status == 'failed'
        assert failed_run.error_message == 'Connection timeout to dealer website'
        assert failed_run.completed_at is not None

    def test_scrape_run_required_platform(self, session):
        """Test that platform is required."""
        scrape_run = ScrapeRun(status='running')
        session.add(scrape_run)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_scrape_run_repr(self, session):
        """Test ScrapeRun __repr__ method."""
        scrape_run = ScrapeRun(platform='bmw_ota', status='completed')
        session.add(scrape_run)
        session.commit()

        repr_str = repr(scrape_run)
        assert 'bmw_ota' in repr_str
        assert 'completed' in repr_str
        assert str(scrape_run.id) in repr_str

    def test_multiple_scrape_runs(self, session):
        """Test creating multiple scrape runs."""
        # Create first run
        run1 = ScrapeRun(platform='bmw_ota', status='completed', vehicles_scraped=100)
        session.add(run1)

        # Create second run
        run2 = ScrapeRun(platform='bmw_ota', status='running', vehicles_scraped=50)
        session.add(run2)

        session.commit()

        # Verify both exist
        runs = session.query(ScrapeRun).filter_by(platform='bmw_ota').all()
        assert len(runs) == 2

    def test_scrape_run_query_by_status(self, session):
        """Test querying scrape runs by status."""
        # Create completed run
        run1 = ScrapeRun(platform='bmw_ota', status='completed')
        session.add(run1)

        # Create running run
        run2 = ScrapeRun(platform='bmw_ota', status='running')
        session.add(run2)

        # Create failed run
        run3 = ScrapeRun(platform='bmw_ota', status='failed')
        session.add(run3)

        session.commit()

        # Query by status
        running_runs = session.query(ScrapeRun).filter_by(status='running').all()
        assert len(running_runs) == 1
        assert running_runs[0].id == run2.id

        completed_runs = session.query(ScrapeRun).filter_by(status='completed').all()
        assert len(completed_runs) == 1

        failed_runs = session.query(ScrapeRun).filter_by(status='failed').all()
        assert len(failed_runs) == 1

    def test_scrape_run_with_pid(self, session):
        """Test scrape run creation with PID."""
        scrape_run = ScrapeRun(
            platform='bmw_ota',
            status='running',
            pid=12345
        )
        session.add(scrape_run)
        session.commit()

        assert scrape_run.pid == 12345

        # Verify retrieval
        retrieved = session.query(ScrapeRun).filter_by(id=scrape_run.id).first()
        assert retrieved.pid == 12345

    def test_scrape_run_pid_update(self, session):
        """Test updating PID after creation."""
        # Create without PID
        scrape_run = ScrapeRun(platform='bmw_ota', status='running')
        session.add(scrape_run)
        session.commit()

        assert scrape_run.pid is None

        # Update with PID
        scrape_run.pid = 67890
        session.commit()

        # Verify update
        retrieved = session.query(ScrapeRun).filter_by(id=scrape_run.id).first()
        assert retrieved.pid == 67890

    def test_scrape_run_query_by_pid(self, session):
        """Test querying scrape runs by PID."""
        # Create runs with different PIDs
        run1 = ScrapeRun(platform='bmw_ota', status='running', pid=11111)
        run2 = ScrapeRun(platform='bmw_ota', status='running', pid=22222)
        run3 = ScrapeRun(platform='bmw_ota', status='completed')  # No PID
        session.add_all([run1, run2, run3])
        session.commit()

        # Query by PID
        result = session.query(ScrapeRun).filter_by(pid=11111).first()
        assert result is not None
        assert result.id == run1.id

        # Query for runs with no PID
        no_pid_runs = session.query(ScrapeRun).filter(ScrapeRun.pid.is_(None)).all()
        assert len(no_pid_runs) == 1
        assert no_pid_runs[0].id == run3.id


class TestDatabaseOperations:
    """Test database session and engine operations."""

    def test_get_engine_default(self):
        """Test getting engine with default database URL."""
        engine = get_engine('sqlite:///:memory:')
        assert engine is not None
        engine.dispose()

    def test_get_session(self):
        """Test creating a session from engine."""
        engine = get_engine('sqlite:///:memory:')
        session = get_session(engine)
        assert session is not None
        session.close()
        engine.dispose()

    def test_init_db(self):
        """Test database initialization."""
        engine = init_db('sqlite:///:memory:')
        assert engine is not None

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert 'vehicles' in tables
        assert 'scrape_runs' in tables

        engine.dispose()

    def test_session_rollback(self, session, sample_vehicle_data):
        """Test session rollback on error."""
        # Create valid vehicle
        vehicle1 = Vehicle(**sample_vehicle_data)
        session.add(vehicle1)
        session.commit()

        # Try to create duplicate VIN
        vehicle2 = Vehicle(**sample_vehicle_data)
        session.add(vehicle2)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()

        # Verify only one vehicle exists
        count = session.query(Vehicle).count()
        assert count == 1

    def test_bulk_insert(self, session, sample_vehicle_data):
        """Test inserting multiple vehicles at once."""
        vehicles = []
        for i in range(10):
            data = sample_vehicle_data.copy()
            data['vin'] = f'VIN{i:013d}ABCD'
            data['title'] = f'2024 BMW M{i}'
            vehicles.append(Vehicle(**data))

        session.bulk_save_objects(vehicles)
        session.commit()

        count = session.query(Vehicle).count()
        assert count == 10


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_strings(self, session):
        """Test handling of very long string values."""
        long_title = 'A' * 500  # Max title length
        long_dealer = 'B' * 255  # Max dealer length

        vehicle = Vehicle(
            dealer=long_dealer,
            title=long_title,
            make='BMW',
            model='M4',
            vin='LONGSTRING1234VIN',
            dealer_platform='bmw_ota',
            source_url='https://example.com/vehicle'
        )
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert len(vehicle.title) == 500
        assert len(vehicle.dealer) == 255

    def test_exact_vin_length(self, session, sample_vehicle_data):
        """Test VIN with exactly 17 characters (standard VIN length)."""
        assert len(sample_vehicle_data['vin']) == 17

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert len(vehicle.vin) == 17

    def test_short_vin(self, session, sample_vehicle_data):
        """Test VIN shorter than standard 17 characters."""
        sample_vehicle_data['vin'] = 'SHORT123'

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.vin == 'SHORT123'

    def test_zero_price(self, session, sample_vehicle_data):
        """Test vehicle with zero price."""
        sample_vehicle_data['price'] = 0.0

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.price == 0.0

    def test_negative_price(self, session, sample_vehicle_data):
        """Test vehicle with negative price (should be allowed at DB level)."""
        sample_vehicle_data['price'] = -1000.0

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.price == -1000.0

    def test_null_price(self, session, sample_vehicle_data):
        """Test vehicle with null price."""
        sample_vehicle_data['price'] = None

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.price is None

    def test_high_odometer(self, session, sample_vehicle_data):
        """Test vehicle with very high odometer reading."""
        sample_vehicle_data['odometer'] = 999999

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.odometer == 999999

    def test_unicode_characters(self, session, sample_vehicle_data):
        """Test handling of unicode characters in text fields."""
        sample_vehicle_data['dealer'] = 'BMW München'
        sample_vehicle_data['ext_color'] = 'Bleu de France'
        sample_vehicle_data['int_color'] = 'Café Latte'

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.dealer == 'BMW München'
        assert vehicle.ext_color == 'Bleu de France'
        assert vehicle.int_color == 'Café Latte'

    def test_special_characters_in_vin(self, session, sample_vehicle_data):
        """Test VIN with alphanumeric characters."""
        sample_vehicle_data['vin'] = 'WBA5B1C04HB244691'  # Real BMW VIN format

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.vin == 'WBA5B1C04HB244691'

    def test_json_options_field(self, session, sample_vehicle_data):
        """Test storing JSON in options text field."""
        complex_options = '["ZCW", "494", "776", "ZMT", "322", "508"]'
        sample_vehicle_data['options'] = complex_options

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.options == complex_options

    def test_empty_options(self, session, sample_vehicle_data):
        """Test vehicle with empty options."""
        sample_vehicle_data['options'] = '[]'

        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        assert vehicle.id is not None
        assert vehicle.options == '[]'

    def test_update_timestamps(self, session, sample_vehicle_data):
        """Test that updated_at changes on update."""
        vehicle = Vehicle(**sample_vehicle_data)
        session.add(vehicle)
        session.commit()

        original_updated_at = vehicle.updated_at
        original_created_at = vehicle.created_at

        # Wait a moment and update
        import time
        time.sleep(0.01)

        vehicle.price = 80000.00
        session.commit()

        session.refresh(vehicle)

        # updated_at should change, created_at should not
        assert vehicle.updated_at > original_updated_at
        assert vehicle.created_at == original_created_at

    def test_concurrent_price_updates(self, engine, sample_vehicle_data):
        """Test handling concurrent updates to the same vehicle."""
        # Create vehicle in first session
        Session = sessionmaker(bind=engine)
        session1 = Session()
        vehicle = Vehicle(**sample_vehicle_data)
        session1.add(vehicle)
        session1.commit()
        vin = vehicle.vin
        session1.close()

        # Open two sessions
        session2 = Session()
        session3 = Session()

        # Both sessions load the same vehicle
        vehicle2 = session2.query(Vehicle).filter_by(vin=vin).first()
        vehicle3 = session3.query(Vehicle).filter_by(vin=vin).first()

        # Both update price
        vehicle2.price = 81000.00
        vehicle3.price = 82000.00

        # First commit succeeds
        session2.commit()

        # Second commit also succeeds (last write wins)
        session3.commit()

        # Verify final state
        session4 = Session()
        final_vehicle = session4.query(Vehicle).filter_by(vin=vin).first()
        assert final_vehicle.price == 82000.00

        session2.close()
        session3.close()
        session4.close()
