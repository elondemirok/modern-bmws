"""
Scrapy settings for dealers_scraper project.
"""

import os

BOT_NAME = 'dealers_scraper'

SPIDER_MODULES = ['dealers_scraper.spiders']
NEWSPIDER_MODULE = 'dealers_scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests (reduced for stealth)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (increased for stealth)
DOWNLOAD_DELAY = 5

# Enable cookies for session management
COOKIES_ENABLED = True

# Disable Telemetry
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'dealers_scraper.middlewares.DealersScraperSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'dealers_scraper.middlewares.DealersScraperDownloaderMiddleware': 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'dealers_scraper.pipelines.VehiclePipeline': 300,
}

# Enable Playwright for JavaScript-heavy sites
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
# Use headless mode in Docker/CI environments, headful mode locally for better evasion
PLAYWRIGHT_HEADLESS = os.getenv('PLAYWRIGHT_HEADLESS', 'False').lower() in ('true', '1', 'yes')
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": PLAYWRIGHT_HEADLESS,
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
    ],
}

# AutoThrottle settings (disabled for manual control)
AUTOTHROTTLE_ENABLED = False

# HTTP cache settings (for development)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = 'utf-8'

# ============================================================================
# Logging Configuration
# ============================================================================

# Set the logging level for the entire application
# Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
# INFO level provides a good balance between visibility and noise in production
LOG_LEVEL = 'INFO'

# Enable logging system-wide
# Should be True in production to capture all important events
LOG_ENABLED = True

# Send log output to stdout instead of stderr
# Useful for containerized environments and log aggregation systems
LOG_STDOUT = True

# Custom log format with detailed information for production troubleshooting
# Includes: timestamp, log level, spider name, and the actual message
LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'

# ISO 8601 date format for log timestamps (YYYY-MM-DD HH:MM:SS,mmm)
# Standard format that's parseable by most log analysis tools
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# Stats Collection
# ============================================================================

# Dump stats to logs when spider finishes
# Provides valuable metrics about scraping performance and success rates
STATS_DUMP = True

# Disable telnet console in production for security
# Already set above but documented here for clarity
# TELNETCONSOLE_ENABLED = False

# ============================================================================
# Verbose Logging Control
# ============================================================================

# Control logging verbosity for specific components
# Reduces noise from overly verbose middleware and extensions

# Suppress overly verbose logs from Scrapy's core components
# These can be re-enabled for debugging by setting to DEBUG level
LOG_LEVEL_SCRAPY = 'INFO'

# Playwright-specific logging (separate from Scrapy's log level)
# Note: Playwright logs are controlled via its own mechanisms
# To reduce Playwright verbosity, you can add to PLAYWRIGHT_LAUNCH_OPTIONS:
# "env": {"DEBUG": ""}  # or specific debug namespaces
