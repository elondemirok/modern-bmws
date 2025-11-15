"""
Integration tests for the BMW Dealership Inventory FastAPI application.

Tests all API endpoints including:
- GET /api/vehicles (with filtering and pagination)
- GET /api/stats (statistics calculation)
- GET /api/dealers (dealer list)
- GET /api/models (model list)
- POST /api/scrape (scrape triggering)
- GET /api/status (status endpoint)
- GET /api/health (health check endpoint)
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from dealers_scraper.models import ScrapeRun, Vehicle
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

# Import the app
sys.path.insert(0, str(Path(__file__).parent.parent / 'web'))
from main import app  # noqa: E402


@pytest.fixture
def sample_vehicles(db_session: Session):
    """Create sample vehicle data for testing."""
    vehicles = [
        Vehicle(
            dealer="BMW of North America",
            title="2024 BMW X5 xDrive40i",
            year=2024,
            make="BMW",
            model="X5",
            trim="xDrive40i",
            vin="5UXCR6C04R9S12345",
            msrp=67000.00,
            price=65000.00,
            odometer=100,
            ext_color="Alpine White",
            int_color="Black",
            dealer_platform="dealerrater",
            source_url="https://example.com/vehicle1",
            scraped_at=datetime.utcnow()
        ),
        Vehicle(
            dealer="BMW of Manhattan",
            title="2024 BMW M3 Competition",
            year=2024,
            make="BMW",
            model="M3",
            trim="Competition",
            vin="WBS8M9C09PCP12346",
            msrp=78000.00,
            price=76000.00,
            odometer=50,
            ext_color="Brooklyn Grey",
            int_color="Red",
            dealer_platform="dealerrater",
            source_url="https://example.com/vehicle2",
            scraped_at=datetime.utcnow()
        ),
        Vehicle(
            dealer="BMW of North America",
            title="2023 BMW 3 Series 330i",
            year=2023,
            make="BMW",
            model="3 Series",
            trim="330i",
            vin="WBA5R1C07NBP12347",
            msrp=45000.00,
            price=42000.00,
            odometer=5000,
            ext_color="Jet Black",
            int_color="Cognac",
            dealer_platform="cargurus",
            source_url="https://example.com/vehicle3",
            scraped_at=datetime.utcnow()
        ),
        Vehicle(
            dealer="BMW of Los Angeles",
            title="2024 BMW X7 xDrive40i",
            year=2024,
            make="BMW",
            model="X7",
            trim="xDrive40i",
            vin="5UXCW6C07P9M12348",
            msrp=85000.00,
            price=83000.00,
            odometer=0,
            ext_color="Mineral White",
            int_color="Black",
            dealer_platform="autotrader",
            source_url="https://example.com/vehicle4",
            scraped_at=datetime.utcnow()
        ),
        Vehicle(
            dealer="BMW of Manhattan",
            title="2024 BMW M4 Coupe",
            year=2024,
            make="BMW",
            model="M4",
            trim="Coupe",
            vin="WBS83AJ08PCP12349",
            msrp=75000.00,
            price=72000.00,
            odometer=25,
            ext_color="Isle of Man Green",
            int_color="Black",
            dealer_platform="dealerrater",
            source_url="https://example.com/vehicle5",
            scraped_at=datetime.utcnow()
        ),
    ]

    for vehicle in vehicles:
        db_session.add(vehicle)
    db_session.commit()

    return vehicles


@pytest.fixture
def sample_scrape_runs(db_session: Session):
    """Create sample scrape run data for testing."""
    runs = [
        ScrapeRun(
            platform="dealerrater",
            status="completed",
            vehicles_scraped=150,
            dealers_scraped=10,
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1)
        ),
        ScrapeRun(
            platform="cargurus",
            status="completed",
            vehicles_scraped=200,
            dealers_scraped=15,
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(minutes=30)
        ),
        ScrapeRun(
            platform="autotrader",
            status="running",
            vehicles_scraped=50,
            dealers_scraped=5,
            started_at=datetime.utcnow() - timedelta(minutes=10),
            completed_at=None
        ),
    ]

    for run in runs:
        db_session.add(run)
    db_session.commit()

    return runs


@pytest.mark.asyncio
class TestVehiclesEndpoint:
    """Tests for GET /api/vehicles endpoint."""

    async def test_get_all_vehicles(self, sample_vehicles):
        """Test getting all vehicles without filters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles")

        assert response.status_code == 200
        data = response.json()
        assert 'vehicles' in data
        assert 'count' in data
        assert data['count'] == 5
        assert len(data['vehicles']) == 5

    async def test_filter_by_dealer(self, sample_vehicles):
        """Test filtering vehicles by dealer."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?dealer=BMW of Manhattan")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2
        for vehicle in data['vehicles']:
            assert vehicle['dealer'] == "BMW of Manhattan"

    async def test_filter_by_model(self, sample_vehicles):
        """Test filtering vehicles by model."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?model=M3")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 1
        assert data['vehicles'][0]['model'] == "M3"
        assert data['vehicles'][0]['trim'] == "Competition"

    async def test_filter_by_price_range(self, sample_vehicles):
        """Test filtering vehicles by price range."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?min_price=70000&max_price=80000")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2
        for vehicle in data['vehicles']:
            assert 70000 <= vehicle['price'] <= 80000

    async def test_filter_by_min_price_only(self, sample_vehicles):
        """Test filtering vehicles by minimum price."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?min_price=75000")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2
        for vehicle in data['vehicles']:
            assert vehicle['price'] >= 75000

    async def test_filter_by_max_price_only(self, sample_vehicles):
        """Test filtering vehicles by maximum price."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?max_price=45000")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 1
        assert data['vehicles'][0]['price'] == 42000.00

    async def test_search_by_text(self, sample_vehicles):
        """Test searching vehicles by text."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?search=M3")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] >= 1
        # Should match title containing M3
        assert any('M3' in v['title'] for v in data['vehicles'])

    async def test_search_by_vin(self, sample_vehicles):
        """Test searching vehicles by VIN."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?search=5UXCR6C04R9S12345")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 1
        assert data['vehicles'][0]['vin'] == "5UXCR6C04R9S12345"

    async def test_search_by_color(self, sample_vehicles):
        """Test searching vehicles by color."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?search=Alpine")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] >= 1
        assert any('Alpine' in v['ext_color'] for v in data['vehicles'])

    async def test_pagination_limit(self, sample_vehicles):
        """Test pagination with limit parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2
        assert len(data['vehicles']) == 2

    async def test_combined_filters(self, sample_vehicles):
        """Test combining multiple filters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/vehicles?dealer=BMW of Manhattan&min_price=70000"
            )

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2
        for vehicle in data['vehicles']:
            assert vehicle['dealer'] == "BMW of Manhattan"
            assert vehicle['price'] >= 70000

    async def test_no_results(self, sample_vehicles):
        """Test query that returns no results."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?model=NonExistentModel")

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 0
        assert data['vehicles'] == []

    async def test_vehicle_data_structure(self, sample_vehicles):
        """Test that vehicle data has all required fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?limit=1")

        assert response.status_code == 200
        data = response.json()
        vehicle = data['vehicles'][0]

        # Check all required fields are present
        required_fields = [
            'id', 'dealer', 'title', 'year', 'make', 'model', 'trim',
            'vin', 'msrp', 'price', 'odometer', 'ext_color', 'int_color',
            'dealer_platform', 'source_url', 'scraped_at'
        ]
        for field in required_fields:
            assert field in vehicle

    async def test_ordering_by_price_desc(self, sample_vehicles):
        """Test that vehicles are ordered by price descending."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles")

        assert response.status_code == 200
        data = response.json()
        prices = [v['price'] for v in data['vehicles']]
        assert prices == sorted(prices, reverse=True)


@pytest.mark.asyncio
class TestStatsEndpoint:
    """Tests for GET /api/stats endpoint."""

    async def test_get_stats_with_data(self, sample_vehicles, sample_scrape_runs):
        """Test getting statistics with data."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        assert 'total_vehicles' in data
        assert 'total_dealers' in data
        assert 'last_run' in data

        assert data['total_vehicles'] == 5
        assert data['total_dealers'] == 3  # BMW of North America, Manhattan, Los Angeles

        # Check last run (should be the most recent one - autotrader)
        assert data['last_run'] is not None
        assert data['last_run']['status'] == 'running'
        assert data['last_run']['vehicles_scraped'] == 50

    async def test_get_stats_empty_database(self, test_db_engine):
        """Test getting statistics with empty database."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        assert data['total_vehicles'] == 0
        assert data['total_dealers'] == 0
        assert data['last_run'] is None

    async def test_stats_last_run_structure(self, sample_scrape_runs):
        """Test that last_run has the correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        last_run = data['last_run']
        assert 'started_at' in last_run
        assert 'status' in last_run
        assert 'vehicles_scraped' in last_run

        # Validate ISO format datetime
        assert isinstance(last_run['started_at'], str)
        datetime.fromisoformat(last_run['started_at'])


@pytest.mark.asyncio
class TestDealersEndpoint:
    """Tests for GET /api/dealers endpoint."""

    async def test_get_dealers(self, sample_vehicles):
        """Test getting list of dealers."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/dealers")

        assert response.status_code == 200
        data = response.json()

        assert 'dealers' in data
        assert len(data['dealers']) == 3

        expected_dealers = [
            "BMW of Los Angeles",
            "BMW of Manhattan",
            "BMW of North America"
        ]
        assert sorted(data['dealers']) == sorted(expected_dealers)

    async def test_dealers_alphabetically_sorted(self, sample_vehicles):
        """Test that dealers are sorted alphabetically."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/dealers")

        assert response.status_code == 200
        data = response.json()

        dealers = data['dealers']
        assert dealers == sorted(dealers)

    async def test_get_dealers_empty_database(self, test_db_engine):
        """Test getting dealers from empty database."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/dealers")

        assert response.status_code == 200
        data = response.json()

        assert data['dealers'] == []


@pytest.mark.asyncio
class TestModelsEndpoint:
    """Tests for GET /api/models endpoint."""

    async def test_get_models(self, sample_vehicles):
        """Test getting list of models."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models")

        assert response.status_code == 200
        data = response.json()

        assert 'models' in data
        # Endpoint returns hardcoded BMW models + database models
        # Should have at least 28 hardcoded models
        assert len(data['models']) >= 28

        # Verify sample vehicle models are included
        sample_models = ["X5", "M3", "3 Series", "X7", "M4"]
        for model in sample_models:
            assert model in data['models']

    async def test_models_alphabetically_sorted(self, sample_vehicles):
        """Test that models are sorted alphabetically."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models")

        assert response.status_code == 200
        data = response.json()

        models = data['models']
        assert models == sorted(models)

    async def test_models_no_null_values(self, sample_vehicles):
        """Test that models list doesn't contain null values."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models")

        assert response.status_code == 200
        data = response.json()

        # Should not include None values
        assert None not in data['models']
        # All models should be non-empty strings
        for model in data['models']:
            assert model is not None
            assert isinstance(model, str)
            assert len(model) > 0

    async def test_get_models_empty_database(self, test_db_engine):
        """Test getting models from empty database."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models")

        assert response.status_code == 200
        data = response.json()

        # Even with empty database, should return hardcoded BMW models
        assert len(data['models']) >= 28
        assert 'iX' in data['models']
        assert 'X5' in data['models']


@pytest.mark.asyncio
class TestScrapeEndpoint:
    """Tests for POST /api/scrape endpoint."""

    async def test_trigger_scrape_default(self, test_db_engine):
        """Test triggering scrape with default platform."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scrape", json={})

        assert response.status_code == 200
        data = response.json()

        assert 'scrape_run_id' in data
        assert 'pid' in data
        assert isinstance(data['scrape_run_id'], int)

    async def test_trigger_scrape_specific_platform(self, test_db_engine):
        """Test triggering scrape with specific platform."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scrape", json={"platform": "roadster"})

        assert response.status_code == 200
        data = response.json()

        assert 'scrape_run_id' in data
        assert 'pid' in data

    async def test_trigger_scrape_all_platforms(self, test_db_engine):
        """Test triggering scrape for all platforms."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scrape", json={"platform": "all"})

        assert response.status_code == 200
        data = response.json()

        assert 'scrape_run_id' in data
        assert 'pid' in data


@pytest.mark.asyncio
class TestStatusEndpoint:
    """Tests for GET /api/status endpoint."""

    async def test_get_status_with_runs(self, sample_scrape_runs):
        """Test getting status with existing scrape runs."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/status")

        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert 'platform' in data
        assert 'started_at' in data
        assert 'vehicles_scraped' in data
        assert 'dealers_scraped' in data

        # Should return the most recent run (autotrader)
        assert data['status'] == 'running'
        assert data['platform'] == 'autotrader'
        assert data['vehicles_scraped'] == 50
        assert data['dealers_scraped'] == 5
        assert data['completed_at'] is None
        assert data['error_message'] is None

    async def test_get_status_no_runs(self, test_db_engine):
        """Test getting status with no scrape runs."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/status")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'idle'
        assert 'message' in data
        assert 'No scrapes have been run yet' in data['message']

    async def test_get_status_completed_run(self, db_session):
        """Test getting status with completed run."""
        run = ScrapeRun(
            platform="dealerrater",
            status="completed",
            vehicles_scraped=100,
            dealers_scraped=8,
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow()
        )
        db_session.add(run)
        db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/status")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'completed'
        assert data['completed_at'] is not None

        # Validate ISO format datetime
        datetime.fromisoformat(data['started_at'])
        datetime.fromisoformat(data['completed_at'])

    async def test_get_status_failed_run(self, db_session):
        """Test getting status with failed run."""
        run = ScrapeRun(
            platform="cargurus",
            status="failed",
            vehicles_scraped=10,
            dealers_scraped=1,
            error_message="Connection timeout",
            started_at=datetime.utcnow() - timedelta(minutes=30),
            completed_at=datetime.utcnow() - timedelta(minutes=25)
        )
        db_session.add(run)
        db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/status")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'failed'
        assert data['error_message'] == "Connection timeout"


@pytest.mark.asyncio
class TestErrorCases:
    """Tests for error cases and edge conditions."""

    async def test_invalid_price_parameters(self, sample_vehicles):
        """Test with invalid price parameters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Non-numeric price should be handled by FastAPI validation
            response = await client.get("/api/vehicles?min_price=invalid")

        # FastAPI should return 422 for validation errors
        assert response.status_code == 422

    async def test_negative_limit(self, sample_vehicles):
        """Test with negative limit parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?limit=-1")

        # Should still return 200, SQLAlchemy will handle negative limit
        assert response.status_code == 200

    async def test_very_large_limit(self, sample_vehicles):
        """Test with very large limit parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?limit=999999")

        assert response.status_code == 200
        data = response.json()
        # Should return all available vehicles (5)
        assert data['count'] == 5

    async def test_price_range_inverted(self, sample_vehicles):
        """Test with min_price > max_price."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?min_price=80000&max_price=50000")

        assert response.status_code == 200
        data = response.json()
        # Should return no results
        assert data['count'] == 0

    async def test_empty_search_string(self, sample_vehicles):
        """Test with empty search string."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?search=")

        assert response.status_code == 200
        data = response.json()
        # Empty search should match all (contains empty string)
        assert data['count'] > 0

    async def test_special_characters_in_search(self, sample_vehicles):
        """Test with special characters in search."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/vehicles?search=%")

        assert response.status_code == 200
        # Should handle SQL LIKE special characters safely

    async def test_concurrent_requests(self, sample_vehicles):
        """Test handling concurrent requests."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Make multiple concurrent requests
            responses = await asyncio.gather(
                client.get("/api/vehicles"),
                client.get("/api/stats"),
                client.get("/api/dealers"),
                client.get("/api/models")
            )

        # All should succeed
        for response in responses:
            assert response.status_code == 200


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for GET /api/health endpoint."""

    async def test_health_no_scrapes(self, test_db_engine):
        """Test health endpoint with no scrapes in database."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['database'] == 'connected'
            assert data['scraper_running'] is False
            assert data['scraper_pid'] is None
            assert data['last_scrape'] is None
            assert 'timestamp' in data

    async def test_health_with_completed_scrape(self, db_session: Session):
        """Test health endpoint with completed scrape."""
        # Create completed scrape run
        scrape_run = ScrapeRun(
            platform='roadster',
            status='completed',
            vehicles_scraped=10,
            pid=99999,
            completed_at=datetime.utcnow()
        )
        db_session.add(scrape_run)
        db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['database'] == 'connected'
            assert data['scraper_running'] is False
            assert data['scraper_pid'] is None
            assert data['last_scrape'] is not None
            assert data['last_scrape']['status'] == 'completed'

    async def test_health_with_running_scrape_dead_process(self, db_session: Session):
        """Test health endpoint with running scrape but dead process."""
        # Create running scrape with fake PID
        scrape_run = ScrapeRun(
            platform='roadster',
            status='running',
            vehicles_scraped=5,
            pid=999999  # Fake PID that doesn't exist
        )
        db_session.add(scrape_run)
        db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['database'] == 'connected'
            assert data['scraper_running'] is False  # Process not actually running
            assert data['scraper_pid'] == 999999


@pytest.mark.asyncio
class TestStatusEndpointWithPID:
    """Tests for GET /api/status endpoint with PID tracking."""

    async def test_status_with_pid(self, db_session: Session):
        """Test status endpoint returns PID and auto-recovers dead processes."""
        scrape_run = ScrapeRun(
            platform='roadster',
            status='running',
            pid=12345  # Fake PID that doesn't exist
        )
        db_session.add(scrape_run)
        db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/status")

            assert response.status_code == 200
            data = response.json()
            assert data['pid'] == 12345
            # Auto-recovery should detect the dead process and mark as failed
            assert data['status'] == 'failed'
            assert 'terminated unexpectedly' in data['error_message']

    async def test_status_auto_recovery_dead_process(self, db_session: Session):
        """Test that status endpoint marks dead processes as failed."""
        # Create running scrape with fake PID
        scrape_run = ScrapeRun(
            platform='roadster',
            status='running',
            pid=999999  # Fake PID that doesn't exist
        )
        db_session.add(scrape_run)
        db_session.commit()
        scrape_id = scrape_run.id

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/status")

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'failed'
            assert 'terminated unexpectedly' in data['error_message']

        # Verify database was updated
        db_session.expire_all()
        updated_run = db_session.query(ScrapeRun).filter_by(id=scrape_id).first()
        assert updated_run.status == 'failed'
        assert updated_run.completed_at is not None


# Import asyncio for concurrent test
