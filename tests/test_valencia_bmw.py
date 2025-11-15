"""
Test module for Valencia BMW scraper integration.

This test verifies that Valencia BMW can be scraped correctly.
"""
import pytest
import sys
from pathlib import Path

# Add scraper to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scraper'))

from dealers_scraper.spiders.dealercom_spider import DealercomSpider


class TestValenciaBMW:
    """Test Valencia BMW scraper configuration."""

    def test_valencia_bmw_spider_initialization(self):
        """Test that Valencia BMW spider can be initialized correctly."""
        spider = DealercomSpider(
            dealer_name="Valencia BMW",
            dealer_url="https://www.valenciabmw.com/new-inventory/index.htm",
            model="iX",
            year="2026"
        )

        # Verify spider configuration
        assert spider.dealer_name == "Valencia BMW"
        assert spider.model == "iX"
        assert spider.year == "2026"
        assert "valenciabmw.com" in spider.dealer_url
        # Verify URL includes filters
        assert "year=2026" in spider.dealer_url
        assert "model=iX" in spider.dealer_url
        assert "status=1-1" in spider.dealer_url

    def test_valencia_bmw_url_structure(self):
        """Test that Valencia BMW URL is properly structured."""
        spider = DealercomSpider(
            dealer_name="Valencia BMW",
            dealer_url="https://www.valenciabmw.com/new-inventory/index.htm",
            model="iX",
            year="2026"
        )

        url = spider.dealer_url

        # URL should contain the base domain
        assert "valenciabmw.com" in url

        # URL should contain filter parameters
        assert "year=2026" in url
        assert "model=iX" in url

        # URL should use HTTPS
        assert url.startswith("https://")

    def test_valencia_bmw_platform_detection(self):
        """Test that Valencia BMW is correctly identified as Dealer.com platform."""
        from run_scraper import DEALER_PLATFORM_MAP

        assert "Valencia BMW" in DEALER_PLATFORM_MAP
        assert DEALER_PLATFORM_MAP["Valencia BMW"]["platform"] == "dealercom"
        assert "valenciabmw.com" in DEALER_PLATFORM_MAP["Valencia BMW"]["inventory_url"]

    def test_valencia_bmw_dealer_config(self):
        """Test that Valencia BMW is properly configured in the dealer map."""
        from run_scraper import DealerConfig, DEALER_PLATFORM_MAP

        # Create dealer config
        config = DealerConfig(
            name="Valencia BMW",
            city="Valencia",
            website="https://www.valenciabmw.com",
            phone="(661) 775-1500"
        )

        # Verify it's supported
        assert config.is_supported()
        assert config.platform == "dealercom"
        assert config.inventory_url is not None
        assert "valenciabmw.com" in config.inventory_url
