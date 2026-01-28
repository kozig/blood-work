#!/bin/bash
# Setup script for blood work PDF scraper

echo "=========================================="
echo "🩸 Blood Work PDF Scraper - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
else
    echo "❌ Python3 not found. Please install Python 3.7 or higher."
    exit 1
fi

echo ""
echo "Creating Python virtual environment..."
echo ""

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created"
    else
        echo "❌ Failed to create virtual environment"
        echo "   Try: sudo apt install python3-venv"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -eq 0 ]; then
    echo "✓ Virtual environment activated"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo ""
echo "Installing required packages..."
echo ""

# Install requirements in venv
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi

echo "✓ All packages installed successfully"

echo ""
echo "=========================================="
echo "Running PDF scraper..."
echo "=========================================="
echo ""

# Make script executable
chmod +x scrape_bloodwork_advanced.py

# Run the scraper (using venv's python)
python scrape_bloodwork_advanced.py Reports_librepdf.pdf blood_work_extracted.csv

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "To run the scraper again:"
echo "  source venv/bin/activate"
echo "  python scrape_bloodwork_advanced.py"
echo ""
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo "=========================================="
