"""
Scrapy spider for Roadster platform used by BMW dealerships.

Platform used by:
- BMW of San Francisco (express.bmwsf.com)
- Peter Pan BMW (online.peterpanbmw.com)

Technology: Vue.js with server-side data injection in window.pageData
"""
import json
from urllib.parse import urlencode, urlparse, urlunparse

import scrapy
from scrapy_playwright.page import PageMethod


class RoadsterSpider(scrapy.Spider):
    """Spider for scraping BMW inventory from Roadster platform dealerships."""

    name = 'roadster'

    custom_settings = {
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,  # 60 seconds (increased for slow sites)
    }

    def __init__(self, dealer_name=None, inventory_url=None, model=None, year=None, *args, **kwargs):
        """
        Initialize the spider with dealer configuration.

        Args:
            dealer_name: Name of the dealership (e.g., 'BMW of San Francisco')
            inventory_url: URL to the dealer's inventory page (e.g., 'https://express.bmwsf.com/inventory')
            model: Optional model to filter (e.g., 'iX', '3 Series')
            year: Optional year to filter (defaults to 2026 if model provided)
        """
        super().__init__(*args, **kwargs)

        if not dealer_name or not inventory_url:
            raise ValueError("Both dealer_name and inventory_url are required parameters")

        self.dealer_name = dealer_name
        self.model = model
        self.year = year or '2026' if model else None

        # Build filtered URL if model is provided
        self.inventory_url = self._build_filtered_url(inventory_url, model, self.year)
        self.start_urls = [self.inventory_url]

        self.logger.info(f"Initialized RoadsterSpider for {dealer_name}")
        self.logger.info(f"Inventory URL: {self.inventory_url}")
        if model:
            self.logger.info(f"Filtering for model: {model}, year: {self.year}")

    def _build_filtered_url(self, base_url, model=None, year=None):
        """
        Build inventory URL with optional model and year filters.

        Args:
            base_url: Base inventory URL
            model: BMW model to filter (e.g., 'iX', '3 Series')
            year: Year to filter (e.g., '2026')

        Returns:
            URL with filters appended as query parameters
        """
        if not model and not year:
            return base_url

        # Parse the base URL
        parsed = urlparse(base_url)

        # Build filter parameters
        filters = []
        if model:
            filters.append(('f', f'submodel:{model}'))
        if year:
            filters.append(('f', f'year:{year}'))

        # Encode filters
        query_string = urlencode(filters)

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
        """Generate initial requests with Playwright enabled."""
        import random

        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_page,
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
                        # Wait for Vue.js to initialize and render
                        PageMethod('wait_for_selector', 'body', timeout=15000),
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        # Randomized wait to appear more human-like
                        PageMethod('wait_for_timeout', random.randint(3000, 5000)),
                    ],
                    'playwright_context_kwargs': {
                        'viewport': {'width': 1920, 'height': 1080},
                        'locale': 'en-US',
                        'timezone_id': 'America/Los_Angeles',
                    },
                }
            )

    async def parse(self, response):
        """
        Parse the inventory page and extract vehicle data from window.pageData.

        Args:
            response: Scrapy response object with Playwright page
        """
        import asyncio
        import random

        page = response.meta.get('playwright_page')

        try:
            # Add random delay before extraction to appear more human-like
            await asyncio.sleep(random.uniform(2, 4))

            # Wait for window.pageData to be available and populated
            try:
                await page.wait_for_function(
                    'window.pageData !== undefined && Object.keys(window.pageData || {}).length > 0',
                    timeout=15000
                )
            except Exception as wait_err:
                self.logger.warning(f"window.pageData did not populate within timeout: {wait_err}")

            # Extract window.pageData from the page
            page_data = await page.evaluate('window.pageData')

            if not page_data:
                self.logger.error(f"No window.pageData found on {response.url}")
                return

            # Validate it's a dictionary
            if not isinstance(page_data, dict):
                self.logger.error(
                    f"window.pageData is not a dictionary. Type: {type(page_data)}, "
                    f"Value: {str(page_data)[:500]}"
                )
                return

            # Log page_data structure for debugging
            import json
            pagedata_keys = list(page_data.keys())
            self.logger.info(f"Successfully extracted window.pageData from {response.url}")
            self.logger.debug(f"window.pageData top-level keys: {pagedata_keys}")

            # Log structure sample
            try:
                pagedata_str = json.dumps(page_data, indent=2, default=str)[:2000]
                self.logger.debug(f"window.pageData structure (truncated): {pagedata_str}")
            except Exception as log_err:
                self.logger.debug(f"Could not serialize pageData for logging: {log_err}")

            # Extract vehicle listings from page_data
            vehicles = self._extract_vehicles_from_page_data(page_data, response.url)

            self.logger.info(f"Found {len(vehicles)} vehicles for {self.dealer_name}")

            # Yield each vehicle item
            for vehicle in vehicles:
                yield vehicle

        except Exception as e:
            self.logger.error(f"Error parsing page {response.url}: {e}", exc_info=True)

        finally:
            # Close the Playwright page
            if page:
                await page.close()

    def _extract_vehicles_from_page_data(self, page_data, source_url):
        """
        Extract vehicle listings from window.pageData.

        Args:
            page_data: Parsed window.pageData object
            source_url: Source URL of the inventory page

        Returns:
            List of vehicle items
        """
        vehicles = []

        try:
            # Navigate to the search data structure
            search_data = page_data.get('search', {})

            # Try different possible paths to vehicle data with detailed logging
            vehicle_list = None
            attempted_paths = []

            # Path 1: search.vehicles (PRIMARY for Roadster based on research)
            vehicles_path = search_data.get('vehicles', [])
            attempted_paths.append(('search.vehicles', type(vehicles_path).__name__,
                                  len(vehicles_path) if isinstance(vehicles_path, list) else 'N/A'))
            if vehicles_path and isinstance(vehicles_path, list) and len(vehicles_path) > 0:
                vehicle_list = vehicles_path
                self.logger.info(f"Found {len(vehicle_list)} vehicles at search.vehicles")

            # Path 2: search.new_inventory (common path)
            if not vehicle_list:
                new_inventory_path = search_data.get('new_inventory', [])
                attempted_paths.append(('search.new_inventory', type(new_inventory_path).__name__,
                                      len(new_inventory_path) if isinstance(new_inventory_path, list) else 'N/A'))
                if new_inventory_path and isinstance(new_inventory_path, list) and len(new_inventory_path) > 0:
                    vehicle_list = new_inventory_path
                    self.logger.info(f"Found {len(vehicle_list)} vehicles at search.new_inventory")

            # Path 3: search.results (fallback)
            if not vehicle_list:
                results_path = search_data.get('results', [])
                attempted_paths.append(('search.results', type(results_path).__name__,
                                      len(results_path) if isinstance(results_path, list) else 'N/A'))
                if results_path and isinstance(results_path, list) and len(results_path) > 0:
                    vehicle_list = results_path
                    self.logger.info(f"Found {len(vehicle_list)} vehicles at search.results")

            # Path 4: top-level vehicles
            if not vehicle_list:
                toplevel_vehicles = page_data.get('vehicles', [])
                attempted_paths.append(('vehicles', type(toplevel_vehicles).__name__,
                                      len(toplevel_vehicles) if isinstance(toplevel_vehicles, list) else 'N/A'))
                if toplevel_vehicles and isinstance(toplevel_vehicles, list) and len(toplevel_vehicles) > 0:
                    vehicle_list = toplevel_vehicles
                    self.logger.info(f"Found {len(vehicle_list)} vehicles at top-level vehicles")

            # Path 5: top-level results
            if not vehicle_list:
                toplevel_results = page_data.get('results', [])
                attempted_paths.append(('results', type(toplevel_results).__name__,
                                      len(toplevel_results) if isinstance(toplevel_results, list) else 'N/A'))
                if toplevel_results and isinstance(toplevel_results, list) and len(toplevel_results) > 0:
                    vehicle_list = toplevel_results
                    self.logger.info(f"Found {len(vehicle_list)} vehicles at top-level results")

            # If still nothing found, log all attempted paths
            if not vehicle_list:
                self.logger.error("No vehicle list found in page_data after trying all paths:")
                for path_name, path_type, path_len in attempted_paths:
                    self.logger.error(f"  - {path_name}: type={path_type}, length={path_len}")
                self.logger.error(f"Available top-level keys in page_data: {list(page_data.keys())}")
                if 'search' in page_data and isinstance(search_data, dict):
                    self.logger.error(f"Available keys in search object: {list(search_data.keys())}")
                return vehicles

            # Process each vehicle
            for idx, vehicle_data in enumerate(vehicle_list):
                try:
                    vehicle_item = self._parse_vehicle(vehicle_data, source_url)
                    if vehicle_item:
                        vehicles.append(vehicle_item)
                except Exception as e:
                    self.logger.error(f"Error parsing vehicle {idx + 1}: {e}", exc_info=True)
                    try:
                        import json
                        vehicle_str = json.dumps(vehicle_data, indent=2, default=str)[:2000]
                        self.logger.error(f"Failed vehicle data (truncated): {vehicle_str}")
                    except Exception as log_err:
                        self.logger.error(f"Could not log vehicle data: {log_err}")
                    continue

        except Exception as e:
            self.logger.error(f"Error extracting vehicles from page_data: {e}", exc_info=True)
            try:
                import json
                pagedata_str = json.dumps(page_data, indent=2, default=str)[:5000]
                self.logger.error(f"page_data content (truncated): {pagedata_str}")
            except Exception as log_err:
                self.logger.error(f"Could not log page_data: {log_err}")

        return vehicles

    def _parse_vehicle(self, vehicle_data, source_url):
        """
        Parse individual vehicle data into item format.

        Args:
            vehicle_data: Dictionary containing vehicle information
            source_url: Source URL of the inventory page

        Returns:
            Dictionary with vehicle item fields
        """
        try:
            # Extract VIN (required field)
            vin = vehicle_data.get('vin') or vehicle_data.get('VIN')
            if not vin:
                self.logger.warning(f"Vehicle missing VIN, skipping: {vehicle_data}")
                return None

            # Extract basic information
            year = vehicle_data.get('year')
            make = vehicle_data.get('make', 'BMW')
            model = vehicle_data.get('model') or vehicle_data.get('submodel')
            trim = vehicle_data.get('trim') or vehicle_data.get('series')

            # Build title from components or use provided title
            title = vehicle_data.get('title') or vehicle_data.get('name')
            if not title and year and make and model:
                title = f"{year} {make} {model}"
                if trim:
                    title = f"{title} {trim}"

            # Extract pricing information (Roadster uses 'price' and 'calc_msrp')
            price = self._extract_price(
                vehicle_data.get('price') or
                vehicle_data.get('asking_price') or
                vehicle_data.get('dealer_starting_price')
            )
            msrp = self._extract_price(
                vehicle_data.get('calc_msrp') or
                vehicle_data.get('msrp') or
                vehicle_data.get('original_price')
            )

            # Extract colors (Roadster uses nested objects with 'label' field)
            ext_color_obj = vehicle_data.get('exterior_color', {})
            if isinstance(ext_color_obj, dict):
                ext_color = ext_color_obj.get('label') or ext_color_obj.get('id')
            else:
                ext_color = vehicle_data.get('ext_color') or str(ext_color_obj) if ext_color_obj else None

            int_color_obj = vehicle_data.get('interior_color', {})
            if isinstance(int_color_obj, dict):
                int_color = int_color_obj.get('label') or int_color_obj.get('id')
            else:
                int_color = vehicle_data.get('int_color') or str(int_color_obj) if int_color_obj else None

            # Extract odometer/mileage (Roadster uses 'mileage' not 'odometer')
            odometer = vehicle_data.get('mileage') or vehicle_data.get('odometer')
            if isinstance(odometer, str):
                # Clean odometer string (e.g., "1,234 miles" -> 1234)
                odometer = ''.join(filter(str.isdigit, odometer))
                odometer = int(odometer) if odometer else None
            elif odometer is not None:
                odometer = int(odometer)

            # Extract options if available
            options = vehicle_data.get('options') or vehicle_data.get('packages')
            if isinstance(options, list):
                options = json.dumps(options)
            elif options and not isinstance(options, str):
                options = str(options)

            # Build vehicle detail URL if available
            vehicle_url = vehicle_data.get('url') or vehicle_data.get('detail_url')
            if vehicle_url and not vehicle_url.startswith('http'):
                # Construct full URL from relative path
                from urllib.parse import urljoin
                vehicle_url = urljoin(source_url, vehicle_url)
            else:
                vehicle_url = source_url

            # Create vehicle item
            item = {
                'vin': vin,
                'title': title,
                'dealer': self.dealer_name,
                'dealer_platform': 'Roadster',
                'source_url': vehicle_url,
                'price': price,
                'msrp': msrp,
                'ext_color': ext_color,
                'int_color': int_color,
                'odometer': odometer,
                'year': year,
                'model': model,
                'trim': trim,
                'options': options,
            }

            self.logger.debug(f"Parsed vehicle: {vin} - {title}")
            return item

        except Exception as e:
            self.logger.error(f"Error parsing vehicle: {e}", exc_info=True)
            return None

    def _extract_price(self, price_value):
        """
        Extract numeric price from various formats.

        Args:
            price_value: Price in various formats (string, int, float, dict)

        Returns:
            Float price or None
        """
        if price_value is None:
            return None

        try:
            # If it's already a number
            if isinstance(price_value, (int, float)):
                return float(price_value)

            # If it's a dictionary, look for value key
            if isinstance(price_value, dict):
                price_value = price_value.get('value') or price_value.get('amount')

            # If it's a string, clean and convert
            if isinstance(price_value, str):
                # Remove currency symbols, commas, and whitespace
                price_str = price_value.replace('$', '').replace(',', '').strip()
                # Extract first number found
                import re
                match = re.search(r'[\d.]+', price_str)
                if match:
                    return float(match.group())

            return None

        except Exception as e:
            self.logger.warning(f"Could not extract price from {price_value}: {e}")
            return None

    async def errback_page(self, failure):
        """
        Handle errors during page requests.

        Args:
            failure: Twisted Failure object
        """
        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()

        self.logger.error(f"Error requesting page {failure.request.url}: {failure.value}")
