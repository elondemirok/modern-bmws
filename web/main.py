"""
FastAPI web application for BMW dealership inventory viewer.
"""
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Add scraper path before other imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scraper'))

from dealers_scraper.models import ScrapeRun, Vehicle
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logging_config import setup_logging
from pydantic import BaseModel
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def is_process_running(pid: int) -> bool:
    """
    Check if a process is running given a PID.

    Args:
        pid: Process ID to check

    Returns:
        True if process is running, False otherwise
    """
    if pid is None:
        return False

    try:
        # Send signal 0 to check if process exists (works on Unix/Linux/macOS)
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        # Process doesn't exist or we don't have permission
        return False

app = FastAPI(title="BMW Dealership Inventory")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests and responses.

    Logs:
    - Request method, path, and client IP
    - Request processing duration
    - Response status code
    - Any errors during request processing
    """
    start_time = time.time()

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Log incoming request
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s"
        )

        return response

    except Exception as e:
        # Log error
        duration = time.time() - start_time
        logger.error(
            f"Error processing {request.method} {request.url.path} - "
            f"Duration: {duration:.3f}s - Error: {str(e)}",
            exc_info=True
        )
        raise

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:////data/bmw_inventory.db')
logger.info(f"Connecting to database: {DATABASE_URL}")
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Failed to establish database connection: {str(e)}", exc_info=True)
    raise


@app.get("/")
async def index(request: Request):
    """Serve the main web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/vehicles")
async def get_vehicles(
    dealer: str = None,
    model: str = None,
    min_price: float = None,
    max_price: float = None,
    search: str = None,
    limit: int = 100
):
    """
    Get list of vehicles with optional filters.
    """
    session = SessionLocal()
    try:
        logger.debug(f"Fetching vehicles with filters - dealer: {dealer}, model: {model}, "
                    f"min_price: {min_price}, max_price: {max_price}, search: {search}, limit: {limit}")
        query = session.query(Vehicle)

        # Apply filters
        if dealer:
            query = query.filter(Vehicle.dealer == dealer)
        if model:
            query = query.filter(Vehicle.model == model)
        if min_price is not None:
            query = query.filter(Vehicle.price >= min_price)
        if max_price is not None:
            query = query.filter(Vehicle.price <= max_price)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Vehicle.title.like(search_pattern)) |
                (Vehicle.vin.like(search_pattern)) |
                (Vehicle.dealer.like(search_pattern)) |
                (Vehicle.ext_color.like(search_pattern))
            )

        # Order by price descending
        query = query.order_by(Vehicle.price.desc())

        # Limit results
        vehicles = query.limit(limit).all()

        # Convert to dict
        result = []
        for v in vehicles:
            result.append({
                'id': v.id,
                'dealer': v.dealer,
                'title': v.title,
                'year': v.year,
                'make': v.make,
                'model': v.model,
                'trim': v.trim,
                'vin': v.vin,
                'msrp': v.msrp,
                'price': v.price,
                'odometer': v.odometer,
                'ext_color': v.ext_color,
                'int_color': v.int_color,
                'dealer_platform': v.dealer_platform,
                'source_url': v.source_url,
                'scraped_at': v.scraped_at.isoformat() if v.scraped_at else None,
            })

        logger.debug(f"Successfully fetched {len(result)} vehicles")
        return {'vehicles': result, 'count': len(result)}

    except Exception as e:
        logger.error(f"Error fetching vehicles: {str(e)}", exc_info=True)
        raise
    finally:
        session.close()


@app.get("/api/stats")
async def get_stats():
    """Get summary statistics."""
    session = SessionLocal()
    try:
        total_vehicles = session.query(func.count(Vehicle.id)).scalar()
        dealers = session.query(func.count(func.distinct(Vehicle.dealer))).scalar()

        # Get last scrape run
        last_run = session.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).first()

        return {
            'total_vehicles': total_vehicles,
            'total_dealers': dealers,
            'last_run': {
                'started_at': last_run.started_at.isoformat() if last_run else None,
                'status': last_run.status if last_run else None,
                'vehicles_scraped': last_run.vehicles_scraped if last_run else 0,
            } if last_run else None
        }

    finally:
        session.close()


@app.get("/api/dealers")
async def get_dealers():
    """Get list of unique dealers."""
    session = SessionLocal()
    try:
        dealers = session.query(Vehicle.dealer).distinct().order_by(Vehicle.dealer).all()
        return {'dealers': [d[0] for d in dealers]}
    finally:
        session.close()


@app.get("/api/models")
async def get_models():
    """Get list of unique BMW models."""
    # Define comprehensive list of BMW models
    # This ensures all models are available even if not in database yet
    bmw_models = [
        '2 Series',
        '3 Series',
        '4 Series',
        '5 Series',
        '7 Series',
        '8 Series',
        'i4',
        'i5',
        'i7',
        'iX',
        'M2',
        'M3',
        'M4',
        'M5',
        'M8',
        'X1',
        'X2',
        'X3',
        'X3 M',
        'X4',
        'X4 M',
        'X5',
        'X5 M',
        'X6',
        'X6 M',
        'X7',
        'XM',
        'Z4',
    ]

    # Also get models from database to include any not in the static list
    session = SessionLocal()
    try:
        db_models = session.query(Vehicle.model).distinct().all()
        db_model_list = [m[0] for m in db_models if m[0]]

        # Combine and deduplicate
        all_models = sorted(set(bmw_models + db_model_list))

        return {'models': all_models}
    finally:
        session.close()


class ScrapeRequest(BaseModel):
    """Request model for scraping trigger."""
    platform: str = "all"
    model: str = None


@app.post("/api/scrape")
async def trigger_scrape(request: ScrapeRequest):
    """
    Trigger a scraping job.

    Args:
        request: Scrape request with optional model filter
    """
    logger.info(f"Scraping triggered - platform: {request.platform}, model: {request.model}")
    session = SessionLocal()
    try:
        # Create a new scrape run record
        scrape_run = ScrapeRun(
            platform=request.platform,
            status='running',
            started_at=datetime.utcnow()
        )
        session.add(scrape_run)
        session.commit()
        scrape_run_id = scrape_run.id

        # Build command to run scraper
        scraper_dir = Path(__file__).parent.parent / 'scraper'
        python_executable = sys.executable

        cmd = [
            python_executable,
            str(scraper_dir / 'run_scraper.py'),
            '--limit', '5',
            '--skip-db-init',
        ]

        # Always filter for iX 2026
        cmd.extend(['--model', 'iX'])
        cmd.extend(['--year', '2026'])

        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)

        # Create log file for this scrape run
        log_file_path = logs_dir / f'scraper-{scrape_run_id}.log'
        logger.info(f"Creating log file for scrape run {scrape_run_id}: {log_file_path}")

        # Open log file for subprocess output
        log_file = open(log_file_path, 'w')  # noqa: SIM115

        # Run scraper in background and capture process
        logger.info(f"Starting scraper subprocess with command: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            cwd=str(scraper_dir),
            stdout=log_file,
            stderr=subprocess.STDOUT
        )

        # Store the process ID in the database
        scrape_run.pid = process.pid
        session.commit()

        logger.info(f"Scraper subprocess started - PID: {process.pid}, scrape_run_id: {scrape_run_id}")

        return {
            'status': 'started',
            'scrape_run_id': scrape_run_id,
            'pid': process.pid,
            'message': 'Scraping started for iX 2026',
            'log_file': str(log_file_path)
        }

    except Exception as e:
        logger.error(f"Failed to start scraping: {str(e)}", exc_info=True)
        if 'scrape_run' in locals():
            scrape_run.status = 'failed'
            scrape_run.error_message = str(e)
            scrape_run.completed_at = datetime.utcnow()
            session.commit()

        return {
            'status': 'error',
            'message': f'Failed to start scraping: {str(e)}'
        }

    finally:
        session.close()


@app.get("/api/status")
async def get_status():
    """Get current scraper status with auto-recovery for crashed processes."""
    logger.debug("Status check requested")
    session = SessionLocal()
    try:
        # Get most recent scrape run
        last_run = session.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).first()

        if not last_run:
            logger.debug("No scrapes have been run yet")
            return {'status': 'idle', 'message': 'No scrapes have been run yet'}

        # Auto-recovery: Check if process is actually still running
        if last_run.status == 'running' and last_run.pid and not is_process_running(last_run.pid):
            # Process crashed - mark as failed
            logger.warning(f"Process {last_run.pid} terminated unexpectedly - marking as failed")
            last_run.status = 'failed'
            last_run.error_message = f'Process {last_run.pid} terminated unexpectedly'
            last_run.completed_at = datetime.utcnow()
            session.commit()

        logger.debug(f"Status check result - status: {last_run.status}, pid: {last_run.pid}")

        return {
            'status': last_run.status,
            'platform': last_run.platform,
            'pid': last_run.pid,
            'started_at': last_run.started_at.isoformat(),
            'completed_at': last_run.completed_at.isoformat() if last_run.completed_at else None,
            'vehicles_scraped': last_run.vehicles_scraped,
            'dealers_scraped': last_run.dealers_scraped,
            'error_message': last_run.error_message,
        }

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        raise
    finally:
        session.close()


@app.get("/api/health")
async def get_health():
    """Get health status and scraper process status."""
    logger.debug("Health check requested")
    session = SessionLocal()
    try:
        # Check database connectivity
        last_run = session.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).first()

        # Determine if scraper is currently running
        scraper_running = False
        process_pid = None
        if last_run and last_run.status == 'running' and last_run.pid:
            scraper_running = is_process_running(last_run.pid)
            process_pid = last_run.pid

        logger.debug(f"Health check result - database: connected, scraper_running: {scraper_running}, pid: {process_pid}")

        return {
            'status': 'healthy',
            'database': 'connected',
            'scraper_running': scraper_running,
            'scraper_pid': process_pid,
            'last_scrape': {
                'id': last_run.id if last_run else None,
                'started_at': last_run.started_at.isoformat() if last_run else None,
                'status': last_run.status if last_run else None,
                'pid': last_run.pid if last_run else None,
            } if last_run else None,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed - database: disconnected, error: {str(e)}", exc_info=True)
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

    finally:
        session.close()
