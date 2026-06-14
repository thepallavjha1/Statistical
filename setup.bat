@echo off
REM Setup script for Statistical Arbitrage Platform (Windows)

echo 📊 Statistical Arbitrage Platform - Setup Script (Windows)
echo ============================================================

REM Check Python version
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create directories
echo Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM Initialize database
echo Initializing database...
python initialize_db.py

REM Run tests
echo.
echo Running tests...
pytest tests\unit\test_core_modules.py -v --tb=short

echo.
echo ✓ Setup completed successfully!
echo.
echo Next steps:
echo 1. Run the Streamlit app: streamlit run streamlit_app/app.py
echo 2. Or run the pipeline: python src/pipeline.py
echo.
pause
