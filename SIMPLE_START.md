# 🚀 Quick Start Guide - Statistical Arbitrage Platform

## Zero-Config Setup (3 Steps)

This is a **simplified version** with everything hardcoded. No .env files, no Docker, no complex setup!

---

## Step 1: Install & Setup (2 minutes)

### Windows:
```bash
# Open Command Prompt and run:
cd C:\Users\Asus\Statistical
setup.bat
```

### Mac/Linux:
```bash
cd ~/Statistical
chmod +x setup.sh
./setup.sh
```

**That's it!** The script will:
- ✓ Create virtual environment
- ✓ Install dependencies
- ✓ Initialize database
- ✓ Generate sample data

---

## Step 2: Run the App (30 seconds)

### Windows:
```bash
venv\Scripts\activate
streamlit run streamlit_app/app.py
```

### Mac/Linux:
```bash
source venv/bin/activate
streamlit run streamlit_app/app.py
```

---

## Step 3: Open in Browser

Navigate to: **http://localhost:8501**

🎉 **You're done!** The dashboard is running locally.

---

## Dashboard Features

### 📊 Home Page
- Overview of latest signals
- Top trading opportunities
- Quick statistics

### 📈 Signals Dashboard  
- Real-time signals for all pairs
- Filter by opportunity strength
- Visual signal distribution

### 🔍 Pair Explorer
- Search any pair (e.g., "RELIANCE-TCS")
- View correlation charts
- Check cointegration results
- See Z-score trends

### 💹 Backtest Page
- Test custom trading strategies
- Set entry/exit thresholds
- View performance metrics:
  - Sharpe Ratio
  - Maximum Drawdown
  - Total Return
  - Hit Rate

### 📊 Analytics Page
- Statistical analysis
- Opportunity rankings
- Download data as CSV

---

## Configuration

All settings are in `config.py` (no need to edit):

```python
# Trading thresholds
LONG_THRESHOLD = -2.0       # Z-score for long signal
SHORT_THRESHOLD = 2.0       # Z-score for short signal
EXIT_THRESHOLD = 0.5        # Z-score for exit

# Data settings
MIN_LIQUIDITY = 1000000     # Min daily volume
CORRELATION_THRESHOLD = 0.7 # Min correlation
COINTEGRATION_PVALUE = 0.05 # Statistical test threshold

# Database
DB_PATH = "data/statarb.db"
DATA_DIR = "data/"
```

To change any setting, just edit `config.py` directly.

---

## Troubleshooting

### "Python not found"
Install Python 3.8+ from https://python.org

### "Module not found" error
Make sure you activated the virtual environment:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

### Database doesn't initialize
```bash
# Manually initialize:
python initialize_db.py
```

### Port 8501 already in use
```bash
# Use different port:
streamlit run streamlit_app/app.py --server.port 8502
```

---

## Next: Deploy to Streamlit Cloud

Once working locally, deploy to the cloud:

### 1. Push to GitHub
```bash
git add .
git commit -m "Working version"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your GitHub repo
4. Set main file: `streamlit_app/app.py`
5. Click "Deploy"

**Your live dashboard is ready!** 🎉

---

## Daily Updates

Your Streamlit Cloud dashboard automatically updates every day at **6 PM IST** via GitHub Actions.

Updates include:
- Latest stock data
- New signals
- Updated backtests
- Performance metrics

Check status at: `https://github.com/yourusername/repo/actions`

---

## File Structure

```
project/
├── config.py                    # All settings here
├── setup.bat / setup.sh        # One-click setup
├── streamlit_app/
│   └── app.py                  # Main dashboard
├── src/
│   ├── data_ingestion/         # Download data
│   ├── pair_selection/         # Find pairs
│   ├── cointegration/          # Test relationships
│   ├── signal_engine/          # Generate signals
│   ├── backtesting/            # Test strategies
│   └── database/               # Data storage
├── data/                        # OHLCV data
│   └── statarb.db              # SQLite database
└── requirements.txt             # Dependencies
```

---

## Common Tasks

### Download fresh data
```bash
python initialize_db.py
```

### Test a specific pair
1. Open dashboard
2. Go to "Pair Explorer"
3. Enter symbols (e.g., RELIANCE, TCS)
4. Click "Analyze"

### Change trading thresholds
1. Open `config.py`
2. Modify `LONG_THRESHOLD`, `SHORT_THRESHOLD`, `EXIT_THRESHOLD`
3. Save and refresh browser

### Add more stocks
1. Edit `config/nifty50.csv`
2. Add stock symbols
3. Restart app

---

## Need Help?

- **Setup issues**: Check `README.md`
- **Configuration**: See `config.py` comments
- **Algorithms**: Read `ALGORITHM.md`
- **Deployment**: Check `DEPLOYMENT.md`

---

## ⚠️ Important Notice

**This platform is for research and analysis ONLY:**
- ❌ NOT investment advice
- ❌ NOT a trading system
- ⚠️ Trade at your own risk
- Always conduct your own due diligence

---

**Enjoy analyzing! 📈**
