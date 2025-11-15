"""
Scrapy spider for Dealer.com platform used by BMW dealerships.

This spider uses Playwright to render JavaScript-heavy pages and extract
vehicle inventory data from the window.DDC.InvData.inventory object.

Example usage:
    scrapy crawl dealercom -a dealer_name="BMW of Mountain View" \
        -a dealer_url="https://www.bmwofmountainview.com/new-inventory/index.htm" \
        -a site_id="bmwofmountainview"
"""
import json
import re
from typing import Any

import scrapy


class DealercomSpider(scrapy.Spider):
    """
    Spider for scraping BMW dealerships using the Dealer.com platform.

    Dealer.com sites store inventory data in window.DDC.InvData.inventory
    after the page loads with JavaScript. This spider uses Playwright to
    render the page and extract that data.
    """

    name = 'dealercom'
    allowed_domains = []  # Set dynamically based on dealer_url

    # Spider configuration parameters
    dealer_name: str | None = None
    dealer_url: str | None = None
    site_id: str | None = None
    model: str | None = None
    year: str | None = None

    # Pagination settings
    items_per_page = 18

    def __init__(self, dealer_name=None, dealer_url=None, site_id=None, model=None, year=None, *args, **kwargs):
        """
        Initialize spider with dealer configuration.

        Args:
            dealer_name: Name of the dealership (e.g., "BMW of Mountain View")
            dealer_url: URL to the new inventory page
            site_id: Site identifier for the dealership (e.g., "bmwofmountainview")
            model: Optional model to filter (e.g., 'iX', '3 Series', 'X5')
            year: Optional year to filter (defaults to 2026 if model provided)
        """
        super().__init__(*args, **kwargs)

        # Set dealer configuration from arguments
        self.dealer_name = dealer_name
        self.model = model
        self.year = year or '2026' if model else None

        # Build filtered URL if model is provided
        self.dealer_url = self._build_filtered_url(dealer_url, model, self.year)
        self.site_id = site_id

        # Validate required parameters
        if not all([self.dealer_name, self.dealer_url]):
            raise ValueError(
                "Missing required parameters. Please provide: "
                "dealer_name, dealer_url"
            )

        # Extract domain from URL for allowed_domains
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', self.dealer_url)
        if domain_match:
            self.allowed_domains = [domain_match.group(1)]

        self.logger.info(f"Initialized spider for {self.dealer_name}")
        self.logger.info(f"Target URL: {self.dealer_url}")
        if model:
            self.logger.info(f"Filtering for model: {model}, year: {self.year}")

    def _build_filtered_url(self, base_url, model=None, year=None):
        """
        Build inventory URL with optional model and year filters.

        Dealer.com sites accept URL parameters like ?year=2026&model=X5&status=1-1

        Args:
            base_url: Base inventory URL
            model: BMW model to filter (e.g., 'iX', '3 Series', 'X5')
            year: Year to filter (e.g., '2026')

        Returns:
            URL with filters appended as query parameters
        """
        if not model and not year:
            # Even without model/year filters, add status=1-1 for in-stock only
            from urllib.parse import urlencode, urlparse, urlunparse
            parsed = urlparse(base_url)
            query_string = urlencode([('status', '1-1')])
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                query_string,
                parsed.fragment
            ))

        from urllib.parse import urlencode, urlparse, urlunparse

        # Parse the base URL
        parsed = urlparse(base_url)

        # Build filter parameters
        params = []
        if year:
            params.append(('year', year))
        if model:
            params.append(('model', model))
        # Always add status=1-1 to filter for in-stock vehicles only
        params.append(('status', '1-1'))

        # Encode parameters
        query_string = urlencode(params)

        # Reconstruct URL with filters
        filtered_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            parsed.fragment
        ))

        return filtered_url

    def start_requests(self):
        """
        Generate initial requests with Playwright enabled.
        """
        import random

        from scrapy_playwright.page import PageMethod

        yield scrapy.Request(
            url=self.dealer_url,
            callback=self.parse,
            errback=self.handle_error,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    # Add stealth script to mask automation
                    PageMethod('add_init_script', '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined,
                        });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                {name: 'Chrome PDF Plugin'},
                                {name: 'Chrome PDF Viewer'},
                                {name: 'Native Client'},
                            ],
                        });
                        window.chrome = {runtime: {}};
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                        });
                    '''),
                    # Wait for DOM to be ready
                    PageMethod('wait_for_selector', 'body', timeout=15000),
                    # Wait for DOM content loaded (faster than networkidle)
                    PageMethod('wait_for_load_state', 'domcontentloaded'),
                    # Randomized wait to appear more human-like
                    PageMethod('wait_for_timeout', random.randint(3000, 6000)),
                ],
                'playwright_context_kwargs': {
                    'viewport': {'width': 1920, 'height': 1080},
                    'locale': 'en-US',
                    'timezone_id': 'America/Los_Angeles',
                },
            },
        )

    async def parse(self, response):
        """
        Parse the inventory page and extract vehicle data from JavaScript object.

        Args:
            response: Scrapy response object with Playwright page
        """
        import asyncio
        import random

        page = response.meta.get('playwright_page')

        try:
            # Add random delay before extraction to appear more human-like
            await asyncio.sleep(random.uniform(2, 4))
            # FIRST: Inspect what's available in the window object
            window_state = await page.evaluate('''
                () => ({
                    has_DDC: typeof window.DDC !== 'undefined',
                    DDC_keys: typeof window.DDC !== 'undefined' ? Object.keys(window.DDC) : [],
                    has_InvData: typeof window.DDC?.InvData !== 'undefined',
                    InvData_keys: typeof window.DDC?.InvData !== 'undefined' ? Object.keys(window.DDC.InvData) : [],
                    has_inventory: typeof window.DDC?.InvData?.inventory !== 'undefined',
                    inventory_type: typeof window.DDC?.InvData?.inventory,
                    inventory_keys: typeof window.DDC?.InvData?.inventory === 'object' ? Object.keys(window.DDC.InvData.inventory) : [],
                    inventory_inventory_type: typeof window.DDC?.InvData?.inventory?.inventory,
                    inventory_inventory_is_array: Array.isArray(window.DDC?.InvData?.inventory?.inventory),
                    inventory_inventory_length: Array.isArray(window.DDC?.InvData?.inventory?.inventory) ? window.DDC.InvData.inventory.inventory.length : 'N/A',
                    inventory_inventory_sample: Array.isArray(window.DDC?.InvData?.inventory?.inventory) && window.DDC.InvData.inventory.inventory.length > 0 ? JSON.stringify(window.DDC.InvData.inventory.inventory[0]).substring(0, 300) : null,
                })
            ''')

            # Log the complete state for debugging
            self.logger.info(f"Window state inspection: {window_state}")

            # Only attempt extraction if object exists
            if not window_state['has_inventory']:
                self.logger.warning(
                    f"Primary path window.DDC.InvData.inventory not found at {response.url}. "
                    f"Window state: {window_state}"
                )
                inventory_data = await self.try_alternative_extraction(page)
            else:
                # Extract the inventory data from window.DDC.InvData.inventory.inventory (nested)
                # The .inventory property is an object with keys: inventory, accounts, incentives, pageInfo
                # The actual vehicle list is in the nested .inventory.inventory property
                inventory_data = await page.evaluate('() => window.DDC.InvData.inventory.inventory')

                self.logger.info(f"Successfully extracted inventory from primary path. Count: {len(inventory_data)}")

            if not inventory_data:
                self.logger.error(
                    f"Failed to extract any inventory data from {response.url}. "
                    f"Final window state: {window_state}"
                )
                await page.close()
                return

            self.logger.info(f"Found {len(inventory_data)} vehicles at {self.dealer_name}")

            # Process each vehicle in the inventory
            for idx, vehicle_data in enumerate(inventory_data):
                try:
                    item = self.parse_vehicle(vehicle_data, response.url)
                    if item:
                        yield item
                except Exception as e:
                    self.logger.error(
                        f"Error parsing vehicle {idx + 1} at {self.dealer_name}: {e}"
                    )
                    self.logger.error(f"Vehicle data type: {type(vehicle_data)}, value: {vehicle_data}")

            # Check if there are more pages
            # Dealer.com typically shows pagination info and next page links
            has_next_page = await self.check_pagination(page, inventory_data)

            if has_next_page:
                # Extract next page URL
                next_page_url = await page.evaluate(
                    '() => document.querySelector(".pagination .next a, .pager-next a")?.href'
                )

                if next_page_url:
                    self.logger.info(f"Following pagination to: {next_page_url}")
                    yield scrapy.Request(
                        url=next_page_url,
                        callback=self.parse,
                        errback=self.handle_error,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_page_methods': [
                                'wait_for_load_state("networkidle")',
                            ],
                        },
                    )

        except Exception as e:
            self.logger.error(f"Error parsing page {response.url}: {e}")

        finally:
            # Always close the page
            if page:
                await page.close()

    async def try_alternative_extraction(self, page):
        """
        Try alternative methods to extract inventory data with detailed logging.

        Some Dealer.com sites may structure the data differently.

        Args:
            page: Playwright page object

        Returns:
            List of vehicle data or empty list
        """
        # First, get detailed window state for debugging
        window_inspection = await page.evaluate('''
            () => {
                const result = {
                    all_window_keys: Object.keys(window).filter(k => k === k.toUpperCase() || k.startsWith('_')).slice(0, 50),
                    DDC_variants: {},
                };

                // Check for various DDC naming conventions
                if (typeof window.DDC !== 'undefined') result.DDC_variants['window.DDC'] = Object.keys(window.DDC);
                if (typeof window._DDC !== 'undefined') result.DDC_variants['window._DDC'] = Object.keys(window._DDC);
                if (typeof window.ddc !== 'undefined') result.DDC_variants['window.ddc'] = Object.keys(window.ddc);
                if (typeof window.inventory !== 'undefined') result.DDC_variants['window.inventory'] = typeof window.inventory;

                return result;
            }
        ''')

        self.logger.warning(f"Alternative extraction - window inspection: {window_inspection}")

        # Try alternative window object paths
        alternatives = [
            ('window.DDC?.inventory', 'Dealer.com variant 1: Direct inventory'),
            ('window.inventory', 'Global inventory object'),
            ('window._DDC?.InvData?.inventory', 'Dealer.com variant 2: Private DDC'),
            ('window.ddc?.InvData?.inventory', 'Lowercase DDC variant'),
            ('window.DDC?.inventoryData', 'Alternative naming: inventoryData'),
            ('window.DDC?.InvData?.vehicles', 'Alternative naming: vehicles plural'),
        ]

        for alt_path, description in alternatives:
            try:
                self.logger.info(f"Attempting alternative extraction: {description}")

                # Attempt evaluation
                data = await page.evaluate(f'() => {alt_path}')

                # Check result explicitly
                if data is None or (isinstance(data, list) and len(data) == 0):
                    self.logger.debug(f"Path {alt_path} returned empty result")
                    continue

                if isinstance(data, list):
                    self.logger.info(
                        f"Found inventory data using alternative path: {description} ({alt_path}). "
                        f"Count: {len(data)}"
                    )
                    return data
                else:
                    self.logger.warning(
                        f"Path {alt_path} returned non-list data: {type(data).__name__}. "
                        f"Sample: {str(data)[:100]}"
                    )

            except Exception as e:
                self.logger.debug(
                    f"Failed to evaluate {alt_path} ({description}): {type(e).__name__}: {e}"
                )
                continue

        self.logger.error(
            f"All alternative extraction paths failed. "
            f"Window inspection data: {window_inspection}"
        )
        return []

    async def check_pagination(self, page, inventory_data):
        """
        Check if there are more pages to scrape.

        Args:
            page: Playwright page object
            inventory_data: Current page inventory data

        Returns:
            bool: True if there are more pages
        """
        try:
            # Check if current page has full page of results
            if len(inventory_data) < self.items_per_page:
                return False

            # Check for next page link
            has_next = await page.evaluate(
                '() => !!document.querySelector(".pagination .next a, .pager-next a")'
            )

            return has_next

        except Exception as e:
            self.logger.warning(f"Error checking pagination: {e}")
            return False

    def parse_vehicle(self, vehicle_data: dict[str, Any], source_url: str) -> dict[str, Any] | None:
        """
        Parse individual vehicle data and return a structured item.

        Args:
            vehicle_data: Raw vehicle data from JavaScript object
            source_url: Source URL where data was scraped

        Returns:
            Dictionary with vehicle data matching pipeline expectations
        """
        # VIN is required - skip if missing
        vin = vehicle_data.get('vin') or vehicle_data.get('VIN')
        if not vin:
            self.logger.warning(f"Skipping vehicle without VIN: {vehicle_data}")
            return None

        # Extract basic vehicle info
        year = self.extract_year(vehicle_data)
        make = vehicle_data.get('make') or vehicle_data.get('Make') or 'BMW'
        model = vehicle_data.get('model') or vehicle_data.get('Model', '')
        trim = vehicle_data.get('trim') or vehicle_data.get('Trim') or vehicle_data.get('series')

        # Convert lists to strings (some Dealer.com sites return lists)
        if isinstance(make, list):
            make = ' '.join(str(x) for x in make if x)
        if isinstance(model, list):
            model = ' '.join(str(x) for x in model if x)
        if isinstance(trim, list):
            trim = ' '.join(str(x) for x in trim if x)

        # Build title from components if not provided
        title = vehicle_data.get('title') or vehicle_data.get('vehicleTitle')
        if isinstance(title, list):
            title = ' '.join(str(x) for x in title if x)
        if not title:
            title = f"{year} {make} {model} {trim}".strip()

        # Extract pricing info
        price = self.extract_price(vehicle_data, 'price', 'sellingPrice', 'internetPrice')
        msrp = self.extract_price(vehicle_data, 'msrp', 'MSRP', 'listPrice')

        # Extract colors
        ext_color = (
            vehicle_data.get('extColor') or
            vehicle_data.get('exteriorColor') or
            vehicle_data.get('ext_color')
        )
        int_color = (
            vehicle_data.get('intColor') or
            vehicle_data.get('interiorColor') or
            vehicle_data.get('int_color')
        )

        # Extract odometer/mileage
        odometer = self.extract_odometer(vehicle_data)

        # Extract options (if available)
        options = vehicle_data.get('options') or vehicle_data.get('packageCodes')
        if options and isinstance(options, (list, dict)):
            options = json.dumps(options)

        # Build the item
        item = {
            'vin': vin,
            'dealer': self.dealer_name,
            'dealer_platform': 'Dealer.com',
            'source_url': source_url,
            'title': title,
            'year': year,
            'model': model,
            'trim': trim,
            'price': price,
            'msrp': msrp,
            'ext_color': ext_color,
            'int_color': int_color,
            'odometer': odometer,
            'options': options,
        }

        self.logger.debug(f"Parsed vehicle: {vin} - {title}")

        return item

    def extract_year(self, vehicle_data: dict[str, Any]) -> int | None:
        """Extract and validate year from vehicle data."""
        year = vehicle_data.get('year') or vehicle_data.get('Year')

        if year:
            try:
                year = int(year)
                # Sanity check: year should be reasonable
                if 1980 <= year <= 2030:
                    return year
            except (ValueError, TypeError):
                pass

        return None

    def extract_price(self, vehicle_data: dict[str, Any], *keys) -> float | None:
        """
        Extract price from vehicle data, trying multiple possible keys.

        Args:
            vehicle_data: Raw vehicle data
            *keys: Possible keys to check for price

        Returns:
            Price as float or None
        """
        for key in keys:
            value = vehicle_data.get(key)
            if value is not None:
                try:
                    # Remove currency symbols and commas
                    if isinstance(value, str):
                        value = re.sub(r'[$,]', '', value)
                    return float(value)
                except (ValueError, TypeError):
                    continue

        return None

    def extract_odometer(self, vehicle_data: dict[str, Any]) -> int | None:
        """Extract and validate odometer reading from vehicle data."""
        odometer = (
            vehicle_data.get('odometer') or
            vehicle_data.get('mileage') or
            vehicle_data.get('miles')
        )

        if odometer is not None:
            try:
                # Remove commas and convert to int
                if isinstance(odometer, str):
                    odometer = re.sub(r'[,]', '', odometer)
                return int(odometer)
            except (ValueError, TypeError):
                pass

        return None

    def handle_error(self, failure):
        """
        Handle request errors.

        Args:
            failure: Twisted Failure object
        """
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
