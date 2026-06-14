# Architecture & Algorithm Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT WEB INTERFACE                      │
│  (Home | Signals | Pair Explorer | Backtest | Analytics)       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     MAIN PIPELINE ORCHESTRATOR                   │
│              (src/pipeline.py - Orchestrates all steps)         │
└──────────────────────────────────────────────────────────────────┘
         │         │              │            │           │
         ▼         ▼              ▼            ▼           ▼
    ┌────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
    │  Data  │ │   Pair    │ │Cointegr- │ │Signal  │ │Backtest  │
    │ Ingest │ │ Selection │ │  ation   │ │Engine  │ │  Engine  │
    └────────┘ └───────────┘ └──────────┘ └────────┘ └──────────┘
         │         │              │            │           │
         └─────────┴──────────────┴────────────┴───────────┘
                              │
                              ▼
         ┌──────────────────────────────────┐
         │   SQLITE DATABASE                │
         │  (Models & Operations)           │
         └──────────────────────────────────┘
         │    │      │        │      │      │
         ▼    ▼      ▼        ▼      ▼      ▼
       Stocks OHLCV Pairs Cointegr Signals Backtest
                           Results         Results
```

---

## Data Flow Diagram

```
┌─────────────┐
│  yfinance   │ ─────┐
└─────────────┘      │
                     ▼
            ┌─────────────────┐
            │ Data Ingestion  │ ───┬──→ Parquet Files (data/)
            │   Manager       │   │
            └─────────────────┘   │
                     │            │
                     └────────────┼──→ Database
                                  │
        ┌─────────────────────────┘
        │
        ▼
   ┌─────────────┐
   │ Stock Data  │
   └─────────────┘
        │
        ├──→ Correlation Analysis
        │    (Pearson > 0.7)
        │
        ├──→ Cointegration Testing
        │    (ADF test, p < 0.05)
        │
        ├──→ Hedge Ratio Calculation
        │    (OLS regression)
        │
        ├──→ Spread Construction
        │    (A - β × B)
        │
        ├──→ Z-Score Calculation
        │    (Rolling statistics)
        │
        ├──→ Signal Generation
        │    (Z-score rules)
        │
        └──→ Backtesting
             (Performance metrics)
```

---

## Core Algorithms

### 1. Cointegration Testing (ADF Test)

**Purpose**: Identify stock pairs with mean-reverting relationships

**Formula**:
$$\Delta y_t = \alpha + \beta t + \gamma y_{t-1} + \sum_{i=1}^p \delta_i \Delta y_{t-i} + \epsilon_t$$

**Rules**:
- Test statistic must be more negative than critical values
- P-value < 0.05 indicates cointegration
- Returns: test statistic, p-value, critical values at 1%, 5%, 10%

**Implementation**: `statsmodels.tsa.stattools.coint()`

---

### 2. Hedge Ratio Calculation (OLS)

**Purpose**: Find optimal ratio for spread construction

**Model**:
$$\text{Stock}_A = \alpha + \beta \times \text{Stock}_B + \epsilon$$

**Calculation**:
```python
X = prices_B.reshape(-1, 1)
y = prices_A.reshape(-1, 1)
model = LinearRegression().fit(X, y)
beta = model.coef_[0, 0]  # Hedge ratio
```

**Spread Formula**:
$$\text{Spread} = \text{Stock}_A - \beta \times \text{Stock}_B$$

---

### 3. Z-Score Calculation

**Purpose**: Measure current deviation from mean

**Formula**:
$$Z = \frac{\text{Spread}_t - \text{Mean(Spread)}}{\text{StdDev(Spread)}}$$

**Rolling Implementation**:
- 30-day window: Recent momentum
- 60-day window: Intermediate term
- 90-day window: Long term

**Python Code**:
```python
rolling_mean = spread[-window:].mean()
rolling_std = spread[-window:].std()
z_score = (spread[-1] - rolling_mean) / rolling_std
```

---

### 4. Signal Generation Rules

**LONG Signal** (Spread is oversold):
```
Condition: Z < -2.0
Action: BUY Stock A, SELL Stock B
Rationale: Spread expected to revert upward
```

**SHORT Signal** (Spread is overbought):
```
Condition: Z > +2.0
Action: SELL Stock A, BUY Stock B
Rationale: Spread expected to revert downward
```

**EXIT Signal** (Mean reversion achieved):
```
Condition: |Z| < 0.5
Action: Close position
Rationale: Trade objective achieved, reduce risk
```

---

### 5. Half-Life Estimation (Ornstein-Uhlenbeck)

**Purpose**: Estimate mean reversion timeframe

**Model**:
$$dx = -k \cdot x \cdot dt + \sigma \cdot dW$$

**Calculation**:
```python
# Autocorrelation at lag-1
rho = sum(spread[:-1] * spread[1:]) / sum(spread^2)

# Mean reversion speed
k = -ln(rho)

# Half-life
half_life = ln(2) / k
```

**Interpretation**: Days expected for spread to revert halfway to mean

---

### 6. Opportunity Scoring

**Composite Score Formula**:
$$\text{Score} = 0.40 \times S_1 + 0.30 \times S_2 + 0.20 \times S_3 + 0.10 \times S_4$$

**Components**:
- $S_1$ = Signal Strength (0-1)
- $S_2$ = Z-Score Extremeness (|Z|/3, capped at 1)
- $S_3$ = Backtest Sharpe Ratio (capped at 1)
- $S_4$ = Cointegration Strength (1 - p_value/0.05, capped at 1)

---

## Backtesting Engine

### Simulation Logic

```
For each trading period:
  1. Calculate current Z-score
  2. Check entry conditions
  3. If entry:
     - Execute trade (buy/sell)
     - Record entry price
     - Record entry date
  4. Check exit conditions
  5. If exit:
     - Close position
     - Calculate P&L
     - Record trade metrics
  6. Update equity curve
```

### Performance Metrics

**Returns**:
```
Total Return = (Final Capital - Initial Capital) / Initial Capital
Annualized Return = Total Return × (365 / Trading Days)
```

**Risk**:
```
Max Drawdown = (Peak - Trough) / Peak
Sharpe Ratio = (Annual Return - Risk-Free Rate) / Annual Volatility
Sortino Ratio = (Annual Return - Risk-Free Rate) / Downside Volatility
```

**Trade Statistics**:
```
Hit Rate = Winning Trades / Total Trades
Profit Factor = Avg Win / Avg Loss
Avg Holding Days = Sum(Holding Days) / Number of Trades
```

---

## Data Quality Checks

### Validation Steps

1. **Completeness Check**
   - Missing OHLCV values < 5%
   - Missing volume < 10%

2. **Logical Checks**
   - High ≥ Open, Close, Low
   - Low ≤ Open, Close, High
   - No negative prices

3. **Spike Detection**
   - Daily move > 20% flagged as outlier
   - Handled in preprocessing

4. **Duplicate Detection**
   - Duplicate dates removed
   - Keep latest value

---

## Database Schema

```
stocks ─────┐
            │
ohlcv_data ─┤
            │
pairs ──────┼─→ cointegration_results
            │    │
            │    ├─→ spread_statistics
            │    │
            │    └─→ signals ─→ signal_history
            │
backtest_results
```

---

## Computational Complexity

| Operation | Complexity | Time (50 stocks) |
|-----------|----------|-----------------|
| Data Download | O(n) | 2-5 min |
| Pair Generation | O(n²) | <1 sec (1,225 pairs) |
| Correlation | O(n×m) | 5-10 sec (3 year lookback) |
| Cointegration | O(n²×m²) | 30-60 sec |
| Signal Generation | O(n²) | 5-10 sec |
| Backtesting | O(n²×m) | 1-2 min |
| **Total** | - | **~5-10 min** |

---

## Edge Cases & Risk Controls

### Handled Edge Cases

1. **Zero Volume Days**
   - Filter during liquidity check
   - Skip in backtest

2. **Corporate Actions**
   - Adjusted by yfinance
   - May cause false breakouts

3. **Market Halts**
   - Creates gaps in data
   - Handled by date alignment

4. **Extreme Volatility**
   - Detected as price spikes
   - Flagged but not excluded

### Risk Controls

1. **Position Sizing**
   - Fixed percentage (95% in backtest)
   - Risk per trade limited

2. **Stop Loss**
   - Exit on Z-score reversal
   - May implement hardstop

3. **Hedging**
   - Beta-weighted hedge ratio
   - Reduces directional risk

---

## Optimization Opportunities

- **Vectorization**: Use numpy/pandas for faster calculations
- **Caching**: Store correlation/cointegration results
- **Parallel Processing**: Process pairs in parallel
- **Distributed Computing**: Use Spark for large universes

---

## References

1. Statsmodels Documentation: https://www.statsmodels.org/
2. Cointegration Theory: Engle & Granger (1987)
3. Mean Reversion: Ornstein-Uhlenbeck Process
4. Pair Trading: Gatev, Goetzmann & Rouwenhorst (2006)

---

For implementation details, see source code in `src/` directory.
