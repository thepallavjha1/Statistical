#!/bin/bash
# Setup script for Statistical Arbitrage Platform

echo "📊 Statistical Arbitrage Platform - Setup Script"
echo "=================================================="

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p data logs config

# Initialize database
echo "Initializing database..."
python initialize_db.py

# Run tests
echo ""
echo "Running tests..."
pytest tests/unit/test_core_modules.py -v --tb=short

echo ""
echo "✓ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run the Streamlit app: streamlit run streamlit_app/app.py"
echo "2. Or run the pipeline: python src/pipeline.py"
echo ""
