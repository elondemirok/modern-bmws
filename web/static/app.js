// BMW Dealership Inventory - Client-side JavaScript

let vehicles = [];
let currentSort = { column: 'price', direction: 'desc' };

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    await loadStats();
    await loadDealers();
    await loadVehicles();
    setupEventListeners();
    updateStatus();
}

// Event listeners
function setupEventListeners() {
    document.getElementById('scrape-btn').addEventListener('click', triggerScrape);
    document.getElementById('filter-btn').addEventListener('click', applyFilters);
    document.getElementById('reset-btn').addEventListener('click', resetFilters);
    document.getElementById('search').addEventListener('keyup', debounce(applyFilters, 500));

    // Table sorting
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.dataset.sort;
            sortTable(column);
        });
    });
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('total-vehicles').textContent = data.total_vehicles || 0;
        document.getElementById('total-dealers').textContent = data.total_dealers || 0;

        if (data.last_run && data.last_run.started_at) {
            const lastUpdate = new Date(data.last_run.started_at);
            document.getElementById('last-update').textContent = formatDateTime(lastUpdate);
        } else {
            document.getElementById('last-update').textContent = 'Never';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load dealers for filter dropdown
async function loadDealers() {
    try {
        const response = await fetch('/api/dealers');
        const data = await response.json();

        const select = document.getElementById('dealer-filter');
        data.dealers.forEach(dealer => {
            const option = document.createElement('option');
            option.value = dealer;
            option.textContent = dealer;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading dealers:', error);
    }
}

// Load vehicles from API
async function loadVehicles(params = {}) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`/api/vehicles?${queryString}`);
        const data = await response.json();

        vehicles = data.vehicles;
        renderTable(vehicles);
        document.getElementById('vehicle-count').textContent =
            `Showing ${vehicles.length} vehicle${vehicles.length !== 1 ? 's' : ''}`;

    } catch (error) {
        console.error('Error loading vehicles:', error);
        showError('Failed to load vehicles');
    }
}

// Render table with vehicles
function renderTable(vehicleList) {
    const tbody = document.getElementById('vehicles-tbody');

    if (vehicleList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No vehicles found</td></tr>';
        return;
    }

    tbody.innerHTML = vehicleList.map(v => `
        <tr>
            <td>${escapeHtml(v.dealer || '')}</td>
            <td>${escapeHtml(v.title || '')}</td>
            <td>${v.year || '-'}</td>
            <td>${formatPrice(v.price)}</td>
            <td>${formatNumber(v.odometer)}</td>
            <td>${escapeHtml(v.ext_color || '-')}</td>
            <td><code>${escapeHtml(v.vin || '')}</code></td>
            <td>${escapeHtml(v.dealer_platform || '')}</td>
            <td><a href="${escapeHtml(v.source_url || '#')}" target="_blank">View</a></td>
        </tr>
    `).join('');
}

// Apply filters
async function applyFilters() {
    const params = {};

    const model = document.getElementById('model-filter').value;
    const dealer = document.getElementById('dealer-filter').value;
    const search = document.getElementById('search').value;
    const minPrice = document.getElementById('min-price').value;
    const maxPrice = document.getElementById('max-price').value;

    if (model) params.model = model;
    if (dealer) params.dealer = dealer;
    if (search) params.search = search;
    if (minPrice) params.min_price = minPrice;
    if (maxPrice) params.max_price = maxPrice;

    await loadVehicles(params);
}

// Reset filters
async function resetFilters() {
    document.getElementById('model-filter').value = '';
    document.getElementById('dealer-filter').value = '';
    document.getElementById('search').value = '';
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    await loadVehicles();
}

// Sort table
function sortTable(column) {
    // Toggle direction if same column
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }

    // Sort vehicles array
    vehicles.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // Handle nulls
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;

        // Compare
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }

        if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });

    // Update UI
    renderTable(vehicles);
    updateSortIndicators();
}

// Update sort indicators in headers
function updateSortIndicators() {
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.sort === currentSort.column) {
            th.classList.add(`sort-${currentSort.direction}`);
        }
    });
}

// Trigger scraping
async function triggerScrape() {
    const button = document.getElementById('scrape-btn');

    button.disabled = true;
    button.textContent = 'Scraping...';

    try {
        const requestBody = {
            platform: 'all',
            model: 'iX'
        };

        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.status === 'not_implemented') {
            alert(data.message);
        } else if (data.status === 'started') {
            // Update UI to show scraping started
            const statusEl = document.getElementById('status');
            statusEl.textContent = data.message;
            statusEl.style.background = '#fff3cd';

            // Poll for status updates
            pollStatus();
        } else if (data.status === 'error') {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error triggering scrape:', error);
        showError('Failed to trigger scraping');
    } finally {
        button.disabled = false;
        button.textContent = 'Scrape Now';
    }
}

// Update status
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const statusEl = document.getElementById('status');
        statusEl.textContent = `Status: ${data.status || 'idle'}`;

        if (data.status === 'running') {
            statusEl.style.background = '#fff3cd';
        } else if (data.status === 'completed') {
            statusEl.style.background = '#d4edda';
        } else if (data.status === 'failed') {
            statusEl.style.background = '#f8d7da';
        } else {
            statusEl.style.background = '#f0f0f0';
        }
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Poll status during scraping
function pollStatus() {
    const interval = setInterval(async () => {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.status !== 'running') {
            clearInterval(interval);
            await loadStats();
            await loadVehicles();
        }

        updateStatus();
    }, 5000); // Poll every 5 seconds
}

// Utility functions
function formatPrice(price) {
    if (!price) return '-';
    return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatNumber(num) {
    if (!num) return '-';
    return num.toLocaleString('en-US');
}

function formatDateTime(date) {
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / 1000 / 60 / 60);

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;

    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showError(message) {
    // Simple error display - could be enhanced
    const tbody = document.getElementById('vehicles-tbody');
    tbody.innerHTML = `<tr><td colspan="9" class="loading" style="color: #d9534f;">${escapeHtml(message)}</td></tr>`;
}
