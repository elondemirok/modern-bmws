"""
Centralized logging configuration for BMW Finder application.

This module provides production-grade logging configuration with support for:
- JSON (production) and formatted (development) output
- Rotating file handlers with configurable retention
- Multiple loggers for different components
- Environment-based configuration

Environment Variables:
    ENV: Environment mode ('production' or 'development', defaults to 'development')
    LOG_LEVEL: Override default log level (optional)
"""

import json
import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs log records as JSON with timestamp, level, logger name, message,
    and any extra fields passed to the logger.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields (any fields not in the standard LogRecord)
        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname',
            'process', 'processName', 'relativeCreated', 'thread', 'threadName',
            'exc_info', 'exc_text', 'stack_info', 'taskName'
        }

        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                log_data[key] = value

        return json.dumps(log_data)


def get_log_directory(environment: str) -> Path:
    """
    Get the appropriate log directory based on environment.

    Args:
        environment: The environment mode ('production' or 'development')

    Returns:
        Path object for the log directory

    Raises:
        OSError: If the log directory cannot be created
    """
    if environment == 'production':
        log_dir = Path('/var/log/bmw-finder')
    else:
        # Use ./logs relative to the project root
        project_root = Path(__file__).parent.parent
        log_dir = project_root / 'logs'

    # Create directory if it doesn't exist
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # Fallback to /tmp if we can't create the directory
        fallback_dir = Path('/tmp/bmw-finder-logs')
        print(
            f"Warning: Could not create log directory {log_dir}: {e}. "
            f"Using fallback: {fallback_dir}",
            file=sys.stderr
        )
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir

    return log_dir


def get_logging_config(environment: str, log_dir: Path) -> dict[str, Any]:
    """
    Generate logging configuration dictionary based on environment.

    Args:
        environment: The environment mode ('production' or 'development')
        log_dir: Path to the log directory

    Returns:
        Configuration dictionary for logging.config.dictConfig
    """
    # Determine formatter based on environment
    formatter_type = 'json' if environment == 'production' else 'detailed'

    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': (
                    '%(asctime)s - %(name)s - %(levelname)s - '
                    '%(module)s:%(funcName)s:%(lineno)d - %(message)s'
                ),
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'json': {
                '()': JSONFormatter,
            },
            'simple': {
                'format': '%(levelname)s - %(name)s - %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': formatter_type,
                'stream': 'ext://sys.stdout',
            },
            'app_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': formatter_type,
                'filename': str(log_dir / 'app.log'),
                'maxBytes': 50 * 1024 * 1024,  # 50 MB
                'backupCount': 10,
                'encoding': 'utf-8',
            },
            'scraper_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': formatter_type,
                'filename': str(log_dir / 'scraper.log'),
                'maxBytes': 100 * 1024 * 1024,  # 100 MB
                'backupCount': 20,
                'encoding': 'utf-8',
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': formatter_type,
                'filename': str(log_dir / 'error.log'),
                'maxBytes': 50 * 1024 * 1024,  # 50 MB
                'backupCount': 10,
                'encoding': 'utf-8',
            },
        },
        'loggers': {
            # Root logger - catches everything not caught by other loggers
            '': {
                'level': 'INFO',
                'handlers': ['console', 'app_file', 'error_file'],
                'propagate': False,
            },
            # Scraper-specific logger
            'scraper': {
                'level': 'DEBUG',
                'handlers': ['console', 'scraper_file', 'error_file'],
                'propagate': False,
            },
            # Scrapy framework logger
            'scrapy': {
                'level': 'INFO',
                'handlers': ['console', 'scraper_file', 'error_file'],
                'propagate': False,
            },
            # Web server/API logger
            'web': {
                'level': 'INFO',
                'handlers': ['console', 'app_file', 'error_file'],
                'propagate': False,
            },
            # Suppress overly verbose third-party loggers
            'urllib3': {
                'level': 'WARNING',
                'handlers': ['app_file'],
                'propagate': False,
            },
            'requests': {
                'level': 'WARNING',
                'handlers': ['app_file'],
                'propagate': False,
            },
        },
    }

    # Override log levels from environment if specified
    log_level = os.getenv('LOG_LEVEL')
    if log_level:
        try:
            level = getattr(logging, log_level.upper())
            config['loggers']['']['level'] = level
            config['handlers']['console']['level'] = level
        except AttributeError:
            print(
                f"Warning: Invalid LOG_LEVEL '{log_level}'. Using default levels.",
                file=sys.stderr
            )

    return config


def setup_logging(logger_name: str | None = None) -> logging.Logger:
    """
    Configure logging for the BMW Finder application.

    This function:
    1. Detects the environment (dev vs production)
    2. Creates the appropriate log directory
    3. Configures logging based on environment
    4. Returns a logger instance

    Args:
        logger_name: Name of the logger to return. If None, returns root logger.
                    Common values: 'scraper', 'web', 'scrapy'

    Returns:
        Configured logger instance

    Raises:
        ValueError: If logging configuration fails

    Example:
        >>> logger = setup_logging('scraper')
        >>> logger.info('Scraper started')
        >>> logger.debug('Processing dealer inventory', extra={'dealer': 'BMW of Berkeley'})
    """
    # Detect environment
    environment = os.getenv('ENV', 'development').lower()
    if environment not in ('production', 'development'):
        print(
            f"Warning: Invalid ENV '{environment}'. Defaulting to 'development'.",
            file=sys.stderr
        )
        environment = 'development'

    # Get log directory
    try:
        log_dir = get_log_directory(environment)
    except Exception as e:
        raise ValueError(f"Failed to create log directory: {e}") from e

    # Generate configuration
    config = get_logging_config(environment, log_dir)

    # Apply configuration
    try:
        logging.config.dictConfig(config)
    except Exception as e:
        raise ValueError(f"Failed to configure logging: {e}") from e

    # Log configuration success
    logger = logging.getLogger(logger_name)
    logger.info(
        f"Logging configured for {environment} environment",
        extra={
            'environment': environment,
            'log_directory': str(log_dir),
            'formatter': 'json' if environment == 'production' else 'detailed',
        }
    )

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.

    This is a convenience function for getting loggers after setup_logging()
    has been called.

    Args:
        name: Name of the logger (e.g., 'scraper', 'web', 'scrapy')

    Returns:
        Logger instance

    Example:
        >>> # In your main application startup
        >>> setup_logging()
        >>>
        >>> # In other modules
        >>> from scraper.logging_config import get_logger
        >>> logger = get_logger('scraper')
        >>> logger.info('Processing started')
    """
    return logging.getLogger(name)


if __name__ == '__main__':
    """
    Demonstration and testing of logging configuration.
    """
    # Setup logging
    logger = setup_logging('scraper')

    # Test different log levels
    logger.debug('This is a debug message', extra={'test_id': 123})
    logger.info('This is an info message', extra={'dealer': 'BMW of Berkeley'})
    logger.warning('This is a warning message')
    logger.error('This is an error message', extra={'error_code': 'TEST_ERROR'})

    # Test exception logging
    try:
        raise ValueError('Test exception')
    except ValueError:
        logger.exception('Exception occurred during test')

    # Test other loggers
    web_logger = get_logger('web')
    web_logger.info('Web server started', extra={'port': 8000})

    scrapy_logger = get_logger('scrapy')
    scrapy_logger.info('Scrapy spider initialized', extra={'spider_name': 'bmw_dealer'})

    print('\n--- Logging test completed ---')
    print(f'Environment: {os.getenv("ENV", "development")}')
    print('Check the logs directory for output files')
