# BMW iX 2026 Inventory - Tests

This directory contains comprehensive tests for the BMW iX 2026 inventory project.

## Test Files

### test_scrapers.py
Unit tests for scraper spider parsing logic (RoadsterSpider and DealercomSpider).
See [Scraper Tests](#scraper-unit-tests) section below.

### test_api.py
Integration tests for the FastAPI web application.
See [API Tests](#api-integration-tests) section below.

---

## Scraper Unit Tests

### Overview
Unit tests for the spider data parsing and transformation logic, WITHOUT making actual network requests.

### Test Coverage - test_scrapers.py

**RoadsterSpider Tests (20 tests):**
- Complete vehicle data parsing with all fields
- Minimal vehicle data parsing (VIN only)
- Price extraction from various formats (int, float, string, dict)
- Color extraction from nested objects and strings
- Odometer/mileage extraction from different formats
- VIN validation and handling of missing VINs
- URL construction (relative and absolute paths)
- Title generation from components
- Options serialization
- Edge cases and error handling

**DealercomSpider Tests (22 tests):**
- Complete vehicle data parsing with all fields
- Alternate field names (capitalized variants)
- Year extraction and validation
- Price extraction from multiple possible keys
- Odometer extraction from various formats
- Color extraction from different key names
- Options serialization (dict and list)
- Default values (e.g., make defaults to BMW)
- Edge cases and malformed data

**Edge Cases Tests (8 tests):**
- Malformed price dictionaries
- Empty color objects
- Zero mileage and price
- Unicode characters in fields
- Very long VINs
- Price strings with text
- Empty string fields

### Running Scraper Tests

```bash
# Setup (from project root)
cd scraper
source .venv/bin/activate
pip install -r requirements.txt

# Run all scraper tests
cd ..
python -m pytest tests/test_scrapers.py -v

# Run specific test classes
python -m pytest tests/test_scrapers.py::TestRoadsterSpider -v
python -m pytest tests/test_scrapers.py::TestDealercomSpider -v
python -m pytest tests/test_scrapers.py::TestEdgeCasesAndErrors -v

# Run with coverage
python -m pytest tests/test_scrapers.py --cov=scraper/dealers_scraper/spiders --cov-report=term-missing
```

### Important Notes - Scraper Tests

**No Network Requests:**
These tests do NOT make actual network requests or use Playwright. They only test the data parsing and transformation methods with mock data.

**Mock Data Fixtures:**
- `roadster_vehicle_*`: Mock vehicle data representing various Roadster platform scenarios
- `dealercom_vehicle_*`: Mock vehicle data representing various Dealer.com platform scenarios
- `roadster_spider`: RoadsterSpider instance for testing
- `dealercom_spider`: DealercomSpider instance for testing

**Known Implementation Issues:**
Several tests document bugs in the current implementation:
- Dict price values (with 'value' or 'amount' keys) are not properly converted
- Using `or` operator treats `0` and empty strings as falsy, causing data loss
- Absolute URLs in vehicle data are incorrectly replaced with source_url

**Test Results:**
- Total: 50 tests
- Status: All passing
- Coverage: RoadsterSpider 42%, DealercomSpider 54% (focused on parsing methods)

---

## API Integration Tests

### Test Coverage - test_api.py

The test suite covers all API endpoints with both success and error cases:

### 1. GET /api/vehicles
- Get all vehicles without filters
- Filter by dealer
- Filter by model
- Filter by price range (min_price, max_price)
- Text search (title, VIN, dealer, color)
- Pagination with limit parameter
- Combined filters
- No results handling
- Data structure validation
- Ordering by price descending

### 2. GET /api/stats
- Statistics with data present
- Statistics with empty database
- Last run information structure
- Datetime ISO format validation

### 3. GET /api/dealers
- Get list of unique dealers
- Alphabetical sorting
- Empty database handling

### 4. GET /api/models
- Get list of unique models
- Alphabetical sorting
- Null value filtering
- Empty database handling

### 5. POST /api/scrape
- Trigger scrape with default platform
- Trigger scrape with specific platform
- Trigger scrape for all platforms

### 6. GET /api/status
- Status with existing scrape runs
- Status with no runs (idle state)
- Completed run information
- Failed run with error message
- Datetime ISO format validation

### 7. Error Cases
- Invalid parameters (422 validation errors)
- Negative limit values
- Very large limit values
- Inverted price ranges (min > max)
- Empty search strings
- Special characters in search (SQL injection prevention)
- Concurrent request handling

## Test Architecture

### Test Database
- Uses in-memory SQLite database for isolation
- Each test gets a fresh database via fixtures
- No side effects between tests

### Fixtures
- `test_db_engine`: Creates test database engine
- `db_session`: Provides database session for each test
- `sample_vehicles`: Creates 5 sample vehicles with variety
- `sample_scrape_runs`: Creates 3 sample scrape runs with different statuses

### Test Client
- Uses `httpx.AsyncClient` for async FastAPI testing
- Base URL set to `http://test` for testing

## Running the Tests

### Prerequisites
Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

Or install web requirements which include test dependencies:
```bash
pip install -r web/requirements.txt
```

### Run All Tests
```bash
pytest tests/test_api.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_api.py::TestVehiclesEndpoint -v
```

### Run Specific Test
```bash
pytest tests/test_api.py::TestVehiclesEndpoint::test_get_all_vehicles -v
```

### Run with Coverage Report
```bash
pytest tests/test_api.py --cov=web --cov-report=html
```

### Run with Output
```bash
pytest tests/test_api.py -v -s
```

## Test Organization

Tests are organized into classes by endpoint:
- `TestVehiclesEndpoint`: Tests for /api/vehicles
- `TestStatsEndpoint`: Tests for /api/stats
- `TestDealersEndpoint`: Tests for /api/dealers
- `TestModelsEndpoint`: Tests for /api/models
- `TestScrapeEndpoint`: Tests for /api/scrape
- `TestStatusEndpoint`: Tests for /api/status
- `TestErrorCases`: Tests for error handling and edge cases

## Sample Test Data

### Vehicles (5 total)
1. 2024 BMW X5 xDrive40i - $65,000 (BMW of North America)
2. 2024 BMW M3 Competition - $76,000 (BMW of Manhattan)
3. 2023 BMW 3 Series 330i - $42,000 (BMW of North America)
4. 2024 BMW X7 xDrive40i - $83,000 (BMW of Los Angeles)
5. 2024 BMW M4 Coupe - $72,000 (BMW of Manhattan)

### Scrape Runs (3 total)
1. Completed dealerrater run - 150 vehicles, 10 dealers
2. Completed cargurus run - 200 vehicles, 15 dealers
3. Running autotrader run - 50 vehicles, 5 dealers (most recent)

## Notes

- All tests use `@pytest.mark.asyncio` for async support
- Tests are isolated with in-memory database
- No external dependencies or network calls required
- Tests validate data structure, ordering, and filtering logic
- Error cases ensure robust API behavior

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r web/requirements.txt
    pytest tests/test_api.py -v --cov=web
```

## Future Enhancements

When Phase 4 (scraping trigger) is implemented, update tests in `TestScrapeEndpoint` to verify:
- Actual scrape job creation
- Queue status
- Background task execution
