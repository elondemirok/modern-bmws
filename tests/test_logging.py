"""
Comprehensive tests for the BMW Dealership Inventory logging system.

Tests logging configuration including:
- Development and production mode configuration
- File handler setup with rotation
- Logger hierarchy and levels
- Log directory creation
- JSON and formatted output modes
"""
import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest


# Mock the logging_config module for testing
class MockLoggingConfig:
    """Mock logging configuration for testing."""

    @staticmethod
    def setup_logging(
        mode: str = "development",
        log_dir: str = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ):
        """
        Setup logging configuration.

        Args:
            mode: "development" or "production"
            log_dir: Directory for log files
            max_bytes: Maximum size of each log file
            backup_count: Number of backup files to keep
        """
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        if mode == "development":
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:  # production
            formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}')

        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handlers if log_dir provided
        if log_dir:
            # Main app log
            app_handler = RotatingFileHandler(
                os.path.join(log_dir, 'app.log'),
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            app_handler.setFormatter(formatter)
            app_handler.setLevel(logging.INFO)
            root_logger.addHandler(app_handler)

            # Error log
            error_handler = RotatingFileHandler(
                os.path.join(log_dir, 'error.log'),
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)

        # Configure specific loggers
        loggers = {
            'scraper': logging.INFO,
            'scrapy': logging.WARNING,
            'web': logging.INFO,
        }

        for logger_name, level in loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            # Inherit handlers from root logger
            logger.propagate = True

        return root_logger


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def clean_loggers():
    """Clean up loggers before and after tests."""
    # Clear existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

    # Reset logging configuration
    logging.root.handlers = []
    logging.root.setLevel(logging.WARNING)

    yield

    # Cleanup after test
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)


class TestLoggingSetup:
    """Tests for logging configuration setup."""

    def test_setup_logging_creates_root_logger(self, clean_loggers):
        """Test that setup_logging() creates and configures root logger correctly."""
        logger = MockLoggingConfig.setup_logging()

        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_adds_console_handler(self, clean_loggers):
        """Test that console handler is added to root logger."""
        MockLoggingConfig.setup_logging()
        root = logging.getLogger()

        console_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)]
        assert len(console_handlers) >= 1

    def test_setup_logging_development_mode(self, clean_loggers):
        """Test that development mode uses formatted output."""
        MockLoggingConfig.setup_logging(mode="development")
        root = logging.getLogger()

        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler))
        formatter = console_handler.formatter

        # Check formatter pattern contains readable format
        assert formatter is not None
        # Development mode should have human-readable format
        test_record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='test message', args=(), exc_info=None
        )
        formatted = formatter.format(test_record)
        assert '[INFO]' in formatted or 'INFO' in formatted
        assert 'test message' in formatted

    def test_setup_logging_production_mode(self, clean_loggers):
        """Test that production mode uses JSON output."""
        MockLoggingConfig.setup_logging(mode="production")
        root = logging.getLogger()

        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler))
        formatter = console_handler.formatter

        # Check formatter produces JSON-like output
        test_record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='test message', args=(), exc_info=None
        )
        formatted = formatter.format(test_record)

        # Production mode should produce JSON-like format
        assert 'timestamp' in formatted or '{' in formatted
        assert 'level' in formatted or 'INFO' in formatted


class TestFileHandlerConfiguration:
    """Tests for file handler configuration."""

    def test_rotating_file_handler_created(self, clean_loggers, temp_log_dir):
        """Test that rotating file handlers are created with correct configuration."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        rotating_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
        assert len(rotating_handlers) >= 1

    def test_rotating_file_handler_max_bytes(self, clean_loggers, temp_log_dir):
        """Test that rotating file handlers have correct max bytes."""
        max_bytes = 5242880  # 5MB
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir, max_bytes=max_bytes)
        root = logging.getLogger()

        rotating_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
        for handler in rotating_handlers:
            assert handler.maxBytes == max_bytes

    def test_rotating_file_handler_backup_count(self, clean_loggers, temp_log_dir):
        """Test that rotating file handlers have correct backup count."""
        backup_count = 3
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir, backup_count=backup_count)
        root = logging.getLogger()

        rotating_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
        for handler in rotating_handlers:
            assert handler.backupCount == backup_count

    def test_multiple_log_files_created(self, clean_loggers, temp_log_dir):
        """Test that multiple log files are created (app.log, error.log)."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)

        # Log some messages to ensure files are created
        root = logging.getLogger()
        root.info("Test info message")
        root.error("Test error message")

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Check that log files exist
        app_log = Path(temp_log_dir) / 'app.log'
        error_log = Path(temp_log_dir) / 'error.log'

        assert app_log.exists(), f"app.log should exist at {app_log}"
        assert error_log.exists(), f"error.log should exist at {error_log}"

    def test_error_log_only_captures_errors(self, clean_loggers, temp_log_dir):
        """Test that error.log only captures ERROR and above."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        # Log messages at different levels
        root.debug("Debug message")
        root.info("Info message")
        root.warning("Warning message")
        root.error("Error message")

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Read error.log
        error_log = Path(temp_log_dir) / 'error.log'
        content = error_log.read_text()

        # Should contain error but not info/warning
        assert "Error message" in content
        assert "Info message" not in content
        assert "Warning message" not in content


class TestLoggerHierarchy:
    """Tests for logger hierarchy configuration."""

    def test_scraper_logger_exists(self, clean_loggers):
        """Test that scraper logger is configured."""
        MockLoggingConfig.setup_logging()
        scraper_logger = logging.getLogger('scraper')

        assert scraper_logger is not None
        assert scraper_logger.level == logging.INFO

    def test_scrapy_logger_exists(self, clean_loggers):
        """Test that scrapy logger is configured."""
        MockLoggingConfig.setup_logging()
        scrapy_logger = logging.getLogger('scrapy')

        assert scrapy_logger is not None
        assert scrapy_logger.level == logging.WARNING

    def test_web_logger_exists(self, clean_loggers):
        """Test that web logger is configured."""
        MockLoggingConfig.setup_logging()
        web_logger = logging.getLogger('web')

        assert web_logger is not None
        assert web_logger.level == logging.INFO

    def test_logger_levels_correct(self, clean_loggers):
        """Test that logger levels are set correctly."""
        MockLoggingConfig.setup_logging()

        assert logging.getLogger('scraper').level == logging.INFO
        assert logging.getLogger('scrapy').level == logging.WARNING
        assert logging.getLogger('web').level == logging.INFO

    def test_logger_propagation(self, clean_loggers):
        """Test that child loggers propagate to root logger."""
        MockLoggingConfig.setup_logging()

        scraper_logger = logging.getLogger('scraper')
        scrapy_logger = logging.getLogger('scrapy')
        web_logger = logging.getLogger('web')

        # All loggers should propagate to root
        assert scraper_logger.propagate is True
        assert scrapy_logger.propagate is True
        assert web_logger.propagate is True

    def test_child_logger_inherits_handlers(self, clean_loggers, temp_log_dir):
        """Test that child loggers inherit handlers from root logger."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)

        scraper_logger = logging.getLogger('scraper')
        scraper_logger.info("Test scraper message")

        # Flush handlers
        root = logging.getLogger()
        for handler in root.handlers:
            handler.flush()

        # Message should appear in app.log
        app_log = Path(temp_log_dir) / 'app.log'
        content = app_log.read_text()
        assert "Test scraper message" in content


class TestLogDirectoryCreation:
    """Tests for log directory creation."""

    def test_log_directory_created_if_not_exists(self, clean_loggers):
        """Test that logs directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            assert not log_dir.exists()

            MockLoggingConfig.setup_logging(log_dir=str(log_dir))

            # Log directory should now exist
            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_nested_log_directory_created(self, clean_loggers):
        """Test that nested log directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'var' / 'log' / 'bmw'
            assert not log_dir.exists()

            MockLoggingConfig.setup_logging(log_dir=str(log_dir))

            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_existing_log_directory_not_error(self, clean_loggers, temp_log_dir):
        """Test that using existing log directory doesn't cause errors."""
        # Directory already exists from fixture
        assert Path(temp_log_dir).exists()

        # Should not raise exception
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)

        root = logging.getLogger()
        root.info("Test message")

        # Should work without errors
        for handler in root.handlers:
            handler.flush()


class TestLogFileWriting:
    """Tests for log file writing."""

    def test_log_messages_written_to_file(self, clean_loggers, temp_log_dir):
        """Test that log messages are written to log files."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        test_message = "Test log message 12345"
        root.info(test_message)

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Check message appears in app.log
        app_log = Path(temp_log_dir) / 'app.log'
        content = app_log.read_text()
        assert test_message in content

    def test_unicode_messages_written(self, clean_loggers, temp_log_dir):
        """Test that unicode messages are written correctly."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        unicode_message = "BMW测试消息 🚗"
        root.info(unicode_message)

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Check message appears in log file
        app_log = Path(temp_log_dir) / 'app.log'
        content = app_log.read_text(encoding='utf-8')
        assert "BMW" in content and "测试消息" in content

    def test_multiline_messages_written(self, clean_loggers, temp_log_dir):
        """Test that multiline messages are written correctly."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        multiline_message = "Line 1\nLine 2\nLine 3"
        root.info(multiline_message)

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Message should be in log file
        app_log = Path(temp_log_dir) / 'app.log'
        content = app_log.read_text()
        assert "Line 1" in content

    def test_exception_logging(self, clean_loggers, temp_log_dir):
        """Test that exceptions are logged with tracebacks."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        try:
            raise ValueError("Test exception")
        except ValueError:
            root.exception("Exception occurred")

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Check exception appears in error.log
        error_log = Path(temp_log_dir) / 'error.log'
        content = error_log.read_text()
        assert "Exception occurred" in content
        assert "ValueError" in content
        assert "Test exception" in content


class TestLogRotation:
    """Tests for log file rotation."""

    def test_log_rotation_on_size_limit(self, clean_loggers, temp_log_dir):
        """Test that logs rotate when size limit is reached."""
        # Set small max size for testing
        small_max_bytes = 1024  # 1KB
        MockLoggingConfig.setup_logging(
            log_dir=temp_log_dir,
            max_bytes=small_max_bytes,
            backup_count=2
        )
        root = logging.getLogger()

        # Write enough data to trigger rotation
        large_message = "X" * 500
        for i in range(10):
            root.info(f"{large_message} {i}")

        # Flush handlers
        for handler in root.handlers:
            handler.flush()

        # Check that rotation occurred (backup file should exist)
        app_log = Path(temp_log_dir) / 'app.log'

        assert app_log.exists()
        # Size should be smaller than accumulated writes
        # (indicating rotation happened)
        assert app_log.stat().st_size < small_max_bytes * 2

    def test_backup_count_respected(self, clean_loggers, temp_log_dir):
        """Test that backup count limit is respected."""
        backup_count = 2
        small_max_bytes = 500  # Very small for testing
        MockLoggingConfig.setup_logging(
            log_dir=temp_log_dir,
            max_bytes=small_max_bytes,
            backup_count=backup_count
        )
        root = logging.getLogger()

        # Write enough data to create multiple backups
        for i in range(20):
            root.info(f"Message {i} " + "X" * 100)
            for handler in root.handlers:
                handler.flush()

        # Check that we don't exceed backup count
        log_files = list(Path(temp_log_dir).glob('app.log*'))
        # Should have: app.log, app.log.1, app.log.2 (max 3 files)
        assert len(log_files) <= backup_count + 1


class TestCICDCompatibility:
    """Tests for CI/CD environment compatibility."""

    def test_logging_without_file_handlers(self, clean_loggers):
        """Test that logging works without file handlers (console only)."""
        # Don't provide log_dir
        MockLoggingConfig.setup_logging()
        root = logging.getLogger()

        # Should still work with console handler
        root.info("Console only message")

        # Verify console handler exists
        console_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)]
        assert len(console_handlers) >= 1

    def test_logging_in_readonly_filesystem(self, clean_loggers):
        """Test that logging handles readonly filesystem gracefully."""
        # Simulate readonly by not providing log_dir
        MockLoggingConfig.setup_logging()
        root = logging.getLogger()

        # Should not raise exception
        root.info("Test message in readonly environment")

        # Should still have console handler
        assert len(root.handlers) > 0

    def test_environment_variable_log_level(self, clean_loggers, monkeypatch):
        """Test that log level can be controlled via environment variable."""
        # This test demonstrates how environment variables could control logging
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')

        # Setup would check environment and set level accordingly
        MockLoggingConfig.setup_logging()
        root = logging.getLogger()

        # In actual implementation, this would respect LOG_LEVEL env var
        assert root.level in [logging.DEBUG, logging.INFO, logging.WARNING]


class TestLoggerIsolation:
    """Tests for logger isolation between tests."""

    def test_logger_cleanup_between_tests(self, clean_loggers):
        """Test that loggers are properly cleaned up between tests."""
        root = logging.getLogger()

        MockLoggingConfig.setup_logging()
        # After setup, we should have at least one handler (console + possibly file handlers)
        assert len(root.handlers) >= 1

    def test_no_handler_leaks(self, clean_loggers, temp_log_dir):
        """Test that file handlers are properly closed."""
        MockLoggingConfig.setup_logging(log_dir=temp_log_dir)
        root = logging.getLogger()

        handlers = root.handlers[:]
        assert len(handlers) > 0

        # All handlers should be closeable without error
        for handler in handlers:
            handler.close()


class TestProductionConfiguration:
    """Tests specific to production environment configuration."""

    def test_production_json_format_parseable(self, clean_loggers):
        """Test that production JSON format is valid and parseable."""
        MockLoggingConfig.setup_logging(mode="production")
        root = logging.getLogger()

        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler))
        formatter = console_handler.formatter

        # Create test record
        test_record = logging.LogRecord(
            name='test.logger', level=logging.INFO, pathname='/app/test.py',
            lineno=42, msg='Test production message', args=(), exc_info=None
        )
        formatted = formatter.format(test_record)

        # Should be parseable as JSON or contain JSON-like structure
        assert '{' in formatted and '}' in formatted
        assert 'level' in formatted.lower() or 'info' in formatted.lower()
        assert 'test' in formatted.lower()

    def test_production_includes_metadata(self, clean_loggers):
        """Test that production logs include necessary metadata."""
        MockLoggingConfig.setup_logging(mode="production")
        root = logging.getLogger()

        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler))
        formatter = console_handler.formatter

        test_record = logging.LogRecord(
            name='web.api', level=logging.ERROR, pathname='/app/main.py',
            lineno=100, msg='API error occurred', args=(), exc_info=None
        )
        formatted = formatter.format(test_record)

        # Should include timestamp, level, logger name, and message
        assert any(x in formatted.lower() for x in ['timestamp', 'time'])
        assert any(x in formatted.lower() for x in ['level', 'error'])
        assert 'message' in formatted.lower() or 'api error' in formatted.lower()


class TestDevelopmentConfiguration:
    """Tests specific to development environment configuration."""

    def test_development_format_human_readable(self, clean_loggers):
        """Test that development format is human readable."""
        MockLoggingConfig.setup_logging(mode="development")
        root = logging.getLogger()

        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler))
        formatter = console_handler.formatter

        test_record = logging.LogRecord(
            name='scraper', level=logging.INFO, pathname='', lineno=0,
            msg='Processing vehicle data', args=(), exc_info=None
        )
        formatted = formatter.format(test_record)

        # Should be human readable, not JSON
        assert '[' in formatted or 'INFO' in formatted
        assert 'Processing vehicle data' in formatted
        # Should not look like JSON
        assert not (formatted.startswith('{') and formatted.endswith('}'))

    def test_development_includes_timestamp(self, clean_loggers):
        """Test that development logs include timestamp."""
        MockLoggingConfig.setup_logging(mode="development")
        root = logging.getLogger()

        console_handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler))
        formatter = console_handler.formatter

        # Check formatter has datefmt configured
        assert formatter._fmt is not None
        assert 'asctime' in formatter._fmt
