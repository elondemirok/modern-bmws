# Scraper service Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy scraper code
COPY . .

# Initialize the database on first run
RUN mkdir -p /data

# Default command - keep container running for on-demand scraping
CMD ["tail", "-f", "/dev/null"]
