# Quick Start Guide

Get the Statistical Arbitrage Platform running in 5 minutes!

## 🚀 Option 1: Quick Streamlit Run (Easiest)

### Windows
```bash
# Clone and setup
git clone <repository-url>
cd statarb-platform
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run app
streamlit run streamlit_app/app.py
```

### macOS/Linux
```bash
git clone <repository-url>
cd statarb-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

streamlit run streamlit_app/app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Option 2: Docker (Fastest)

```bash
# Clone
git clone <repository-url>
cd statarb-platform

# Build and run
docker build -t statarb .
docker run -p 8501:8501 -v $(pwd)/data:/app/data statarb
```

Open [http://localhost:8501](http://localhost:8501)

---

## 📊 Option 3: Pipeline Only (No UI)

```bash
# Setup (same as above)
git clone <repository-url>
cd statarb-platform
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python initialize_db.py

# Generate test data
python generate_test_data.py

# Run pipeline
python src/pipeline.py
```

---

## 💡 First Steps

### 1. **Explore the Home Page**
   - See platform overview
   - Check current signals
   - Quick action buttons

### 2. **View Signals Dashboard**
   - Real-time signal updates
   - Filter by type and strength
   - Analyze distributions

### 3. **Search a Pair**
   - Go to "Pair Explorer"
   - Enter stock symbols (e.g., RELIANCE, TCS)
   - View charts and statistics

### 4. **Run a Backtest**
   - Select a pair
   - Set entry/exit thresholds
   - View performance metrics

### 5. **Check Analytics**
   - See opportunity rankings
   - Analyze cointegration results
   - Download data

---

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
