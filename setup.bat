@echo off
REM Setup script for Statistical Arbitrage Platform (Windows)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  Statistical Arbitrage Platform - Windows Setup          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Check Python version
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.

REM Create necessary directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config
echo ✓ Directories created
echo.

REM Initialize database
echo Initializing database...
python initialize_db.py
echo.

echo ╔══════════════════════════════════════════════════════════╗
echo ║  ✓ Setup Complete!                                       ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Next steps:
echo.
echo 1. Run the Streamlit app:
echo    streamlit run streamlit_app/app.py
echo.
echo 2. Open your browser:
echo    http://localhost:8501
echo.
echo.
pause
