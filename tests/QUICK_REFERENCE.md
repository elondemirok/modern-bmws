# API Tests Quick Reference

## Test Statistics
- **Total Test File Size**: 24 KB (730 lines)
- **Total Test Classes**: 7
- **Total Test Methods**: 38
- **Test Fixtures**: 2 (sample_vehicles, sample_scrape_runs)

## Test Breakdown by Endpoint

| Endpoint | Test Class | Tests | Coverage |
|----------|-----------|-------|----------|
| GET /api/vehicles | TestVehiclesEndpoint | 15 | Filtering, search, pagination, ordering |
| GET /api/stats | TestStatsEndpoint | 3 | Statistics, empty DB, data structure |
| GET /api/dealers | TestDealersEndpoint | 3 | List, sorting, empty DB |
| GET /api/models | TestModelsEndpoint | 4 | List, sorting, null handling, empty DB |
| POST /api/scrape | TestScrapeEndpoint | 3 | Default, specific, all platforms |
| GET /api/status | TestStatusEndpoint | 4 | Running, idle, completed, failed |
| Error Cases | TestErrorCases | 7 | Validation, edge cases, security |

## Quick Commands

```bash
# Run all API tests
pytest tests/test_api.py -v

# Run tests for specific endpoint
pytest tests/test_api.py::TestVehiclesEndpoint -v

# Run with coverage
pytest tests/test_api.py --cov=web --cov-report=html

# Run specific test
pytest tests/test_api.py::TestVehiclesEndpoint::test_filter_by_model -v
```

## Sample Data

**5 Vehicles**
- 3 Dealers: BMW of North America, BMW of Manhattan, BMW of Los Angeles
- 5 Models: X5, M3, 3 Series, X7, M4
- Price range: $42,000 - $83,000

**3 Scrape Runs**
- 2 Completed: dealerrater (150 vehicles), cargurus (200 vehicles)
- 1 Running: autotrader (50 vehicles)

## Test Types

### Success Cases (31 tests)
- Valid inputs
- Empty results
- Data validation
- Sorting/ordering

### Error Cases (7 tests)
- Invalid parameters
- Edge cases
- SQL injection prevention
- Concurrent requests

## Integration Points

Uses existing infrastructure:
- `conftest.py` fixtures (db_session, db_engine, test_client)
- SQLAlchemy models (Vehicle, ScrapeRun)
- FastAPI app (web/main.py)
