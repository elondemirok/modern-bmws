"""
Scrapy middlewares for dealers_scraper.
"""
from scrapy import signals


class DealersScraperSpiderMiddleware:
    """Spider middleware for dealers_scraper."""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        yield from result

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        yield from start_requests

    def spider_opened(self, spider):
        spider.logger.info(f'Spider opened: {spider.name}')


class DealersScraperDownloaderMiddleware:
    """Downloader middleware for dealers_scraper."""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info(f'Spider opened: {spider.name}')
