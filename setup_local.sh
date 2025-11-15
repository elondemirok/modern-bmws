#!/bin/bash
# Setup script for running scraper locally on macOS (non-headless mode)

set -e

echo "Setting up local Python environment for BMW scraper..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install scraper requirements
echo "Installing scraper dependencies..."
pip install -r scraper/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers (this may take a few minutes)..."
playwright install chromium

# Create data directory
mkdir -p data
mkdir -p logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the scraper:"
echo "  ./run_local.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  cd scraper && python run_scraper.py --all --model iX --year 2026"
