# ⚡ Quick Start Guide (5 Minutes)

Get the Statistical Arbitrage Platform running on your machine RIGHT NOW!

---

## 🎯 The Fastest Way

### Windows
```bash
cd C:\Users\Asus\Statistical
setup.bat
```

**That's it!** The script handles:
- ✓ Virtual environment setup
- ✓ Dependencies installation
- ✓ Database initialization
- ✓ Sample data generation

### Mac/Linux
```bash
cd ~/Statistical
chmod +x setup.sh
./setup.sh
```

---

## ▶️ Run the Dashboard

### After Setup, Activate Environment

**Windows:**
```bash
venv\Scripts\activate
streamlit run streamlit_app/app.py
```

**Mac/Linux:**
```bash
source venv/bin/activate
streamlit run streamlit_app/app.py
```

---

## 🌐 Open in Browser

Visit: **http://localhost:8501**

That's all! You're running the platform now! 🎉

---

## 📊 What You'll See

### Home Page
- Overview of all signals
- Top opportunities
- Quick statistics

### Signals Dashboard
- All trading signals
- Filters by signal type
- Z-score distribution

### Pair Explorer
- Search any pair
- View charts
- Check cointegration
- Analyze correlations

### Backtest
- Test strategies
- Custom thresholds
- Performance metrics

### Analytics
- Statistical analysis
- Opportunity rankings
- CSV export

---

## 🔧 Customizing

### Change Signal Thresholds
Edit `config.py`:
```python
LONG_THRESHOLD = -2.0    # Change this
SHORT_THRESHOLD = 2.0    # Or this
EXIT_THRESHOLD = 0.5     # Or this
```

Refresh the browser - changes take effect immediately!

---

## ⚠️ Troubleshooting

**"Python not found"**
- Install Python 3.8+ from https://python.org
- Add to PATH during installation

**"Module not found" error**
- Make sure virtual environment is activated:
  - Windows: `venv\Scripts\activate`
  - Mac/Linux: `source venv/bin/activate`

**Port 8501 already in use**
```bash
streamlit run streamlit_app/app.py --server.port 8502
```

**Database error**
```bash
python initialize_db.py
```

---

## 🚀 Next: Deploy to Cloud

Once working locally:

```bash
# Push to GitHub
git add .
git commit -m "Working version"
git push origin main
```

Then:
1. Go to https://share.streamlit.io
2. Create new app
3. Select your repo
4. Set main file: `streamlit_app/app.py`
5. Click Deploy

**Live in 2 minutes!** 🌟

---

## 📚 More Help

- **Full setup**: [SIMPLE_START.md](SIMPLE_START.md)
- **How it works**: [ALGORITHM.md](ALGORITHM.md)
- **Deploy options**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Happy pair trading!** 📈


## 📚 Key Concepts

### 🔗 Cointegration
Two stocks are cointegrated if they move together in the long term. This signals a mean-reverting relationship.

**Signal**: P-value < 0.05 (Augmented Dickey-Fuller test)

### 📈 Z-Score
How many standard deviations away from the mean a spread is.

- **Z < -2**: Long signal (BUY A, SELL B)
- **Z > +2**: Short signal (SELL A, BUY B)
- **|Z| < 0.5**: Exit signal

### 💰 Hedge Ratio
The ratio at which to sell the second stock for every unit of the first stock.

**Formula**: Spread = Stock_A - Beta × Stock_B

---

## ⚙️ Configuration

Most settings are in `src/signal_engine/engine.py`:

```python
long_threshold = -2.0      # Entry long spread
short_threshold = 2.0      # Entry short spread
exit_threshold = 0.5       # Exit position
```

---

## 🧪 Test Everything

```bash
# Run all tests
pytest tests/ -v

# Just unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=src
```

---

## 🐛 Troubleshooting

### "Module not found" error
```bash
# Ensure you're in the right directory
cd statarb-platform

# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
```

### "No data for symbol" error
- Symbols must be NSE format (e.g., RELIANCE.NS)
- Check internet connection
- yfinance may rate-limit after many requests

### Port 8501 already in use
```bash
# Use different port
streamlit run streamlit_app/app.py --server.port 8502
```

### Database locked error
- Close other instances of the app
- Delete corrupted database: `rm data/statarb.db`
- Reinitialize: `python initialize_db.py`

---

## 📞 Getting Help

1. **Read the full README.md** for detailed documentation
2. **Check DEPLOYMENT.md** for deployment options
3. **Review GitHub Issues** for common problems
4. **Check logs** in terminal output

---

## ✨ What's Next?

1. **Deploy to Streamlit Cloud** (free)
2. **Setup GitHub Actions** for daily updates
3. **Explore the codebase** to understand the algorithms
4. **Extend functionality** for your needs
5. **Share your results!**

---

## 🎯 Your First Analysis

```python
from src.pipeline import get_pipeline

# Initialize
pipeline = get_pipeline()

# Run analysis
result = pipeline.run_full_pipeline('config/nifty50.csv')

# Check results
print(f"Cointegrated: {result['cointegrated_pairs']}")
print(f"Signals: {result['active_signals']}")

# Get top opportunities
signals = pipeline.get_latest_signals(top_n=10)
for sig in signals:
    print(f"{sig['stock_a']}/{sig['stock_b']}: {sig['signal']}")
```

---

**Happy Trading!** 🚀

Remember: This is for research and analysis. Always do your own due diligence before trading.
