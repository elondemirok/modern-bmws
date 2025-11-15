"""
Logging configuration for the BMW dealership inventory web application.
"""
import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO"):
    """
    Configure logging for the web application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler for all logs
            logging.FileHandler(logs_dir / 'web.log', mode='a'),
        ]
    )

    # Set logging levels for third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
