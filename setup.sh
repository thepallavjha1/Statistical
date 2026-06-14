#!/bin/bash
# Setup script for Statistical Arbitrage Platform (Unix/Mac)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Statistical Arbitrage Platform - Setup Script           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo ""

# Create directories
mkdir -p data logs config
echo "✓ Directories created"
echo ""

# Initialize database
echo "Initializing database..."
python initialize_db.py
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✓ Setup Complete!                                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Run the Streamlit app:"
echo "   streamlit run streamlit_app/app.py"
echo ""
echo "2. Open your browser:"
echo "   http://localhost:8501"
echo ""
