"""
Virtual trading execution engine.
Manages a persistent virtual portfolio of 1 Crore INR (10,000,000 INR).
Tracks open positions and logs transaction history.
"""

import logging
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from src.database.models import (
    VirtualPortfolio, VirtualPosition, VirtualTradeHistory, DatabaseManager
)
from src.data_ingestion.manager import get_data_manager
from src.cointegration.analyzer import get_cointegration_analyzer

logger = logging.getLogger(__name__)

class VirtualTrader:
    """Manages virtual trading portfolio operations."""
    
    def __init__(self, allocation_per_trade: float = 1000000.0, max_positions: int = 8):
        self.db = DatabaseManager()
        self.data_manager = get_data_manager()
        self.coint_analyzer = get_cointegration_analyzer()
        self.allocation_per_trade = allocation_per_trade  # 10 Lakhs per trade (10% of portfolio)
        self.max_positions = max_positions

    def get_portfolio(self, session: Session) -> VirtualPortfolio:
        """Get or initialize the virtual portfolio."""
        portfolio = session.query(VirtualPortfolio).first()
        if not portfolio:
            portfolio = VirtualPortfolio(
                initial_capital=10000000.0,  # 1 Crore INR
                cash=10000000.0,
                equity=10000000.0,
                last_updated=datetime.utcnow()
            )
            session.add(portfolio)
            session.commit()
            logger.info("Initialized Virtual Portfolio with 1 Crore INR.")
        return portfolio

    def execute_trading_round(self, active_signals: List[Dict]):
        """Run daily virtual trading round: check exits, then entries, and update equity."""
        session = self.db.get_session()
        try:
            # Clean up duplicate portfolios if they exist (safeguard against concurrent worker races)
            portfolios = session.query(VirtualPortfolio).all()
            if len(portfolios) > 1:
                logger.warning(f"Found {len(portfolios)} portfolio records. Keeping only the first one.")
                for p in portfolios[1:]:
                    session.delete(p)
                session.commit()
                
            portfolio = self.get_portfolio(session)
            
            # Clean up duplicate positions if they exist in the database (safeguard against race conditions)
            all_pos = session.query(VirtualPosition).all()
            seen_pairs = set()
            for pos in all_pos:
                pair_key = tuple(sorted([pos.stock_a, pos.stock_b]))
                if pair_key in seen_pairs:
                    logger.warning(f"Found duplicate position in DB for {pos.stock_a}-{pos.stock_b}. Deleting it.")
                    session.delete(pos)
                else:
                    seen_pairs.add(pair_key)
            session.commit()
            
            # Step 1: Manage and Close Positions
            open_positions = session.query(VirtualPosition).all()
            logger.info(f"Checking {len(open_positions)} open virtual positions for exits...")
            
            for pos in open_positions:
                self._check_and_close_position(session, portfolio, pos, active_signals)
            
            # Step 2: Enter New Positions
            # Reload portfolio to get updated cash balance
            session.refresh(portfolio)
            
            current_open_count = session.query(VirtualPosition).count()
            logger.info(f"Current open positions count: {current_open_count}/{self.max_positions}")
            
            for sig in active_signals:
                if current_open_count >= self.max_positions:
                    logger.warning("Max positions limit reached. Skipping new entries.")
                    break
                
                entered = self._check_and_open_position(session, portfolio, sig)
                if entered:
                    current_open_count += 1
            
            # Step 3: Recalculate Portfolio Equity
            session.refresh(portfolio)
            open_positions = session.query(VirtualPosition).all()
            
            total_position_value = 0.0
            for pos in open_positions:
                prices_a = self.data_manager.get_price_series(pos.stock_a)
                prices_b = self.data_manager.get_price_series(pos.stock_b)
                if prices_a is not None and not prices_a.empty and prices_b is not None and not prices_b.empty:
                    current_price_a = prices_a.iloc[-1]
                    current_price_b = prices_b.iloc[-1]
                    pos_val = pos.shares_a * current_price_a + pos.shares_b * current_price_b
                    total_position_value += pos_val
                    logger.debug(f"Position {pos.stock_a}-{pos.stock_b}: value = {pos_val:.2f}")
            
            portfolio.equity = portfolio.cash + total_position_value
            portfolio.last_updated = datetime.utcnow()
            session.commit()
            
            logger.info(f"Virtual Portfolio update completed. Cash: {portfolio.cash:,.2f} INR, Equity: {portfolio.equity:,.2f} INR")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error in virtual trading round: {str(e)}", exc_info=True)
            raise e
        finally:
            session.close()

    def _check_and_close_position(self, session: Session, portfolio: VirtualPortfolio, 
                                  pos: VirtualPosition, active_signals: List[Dict]):
        """Evaluate if an open position should be closed based on exit thresholds."""
        # Find if there is an explicit exit or hold signal for this pair
        sig_match = next((s for s in active_signals if 
                          (s['stock_a'] == pos.stock_a and s['stock_b'] == pos.stock_b) or
                          (s['stock_a'] == pos.stock_b and s['stock_b'] == pos.stock_a)), None)
        
        # Calculate Z-score of spread for current date
        prices_a = self.data_manager.get_price_series(pos.stock_a)
        prices_b = self.data_manager.get_price_series(pos.stock_b)
        
        if prices_a is None or prices_a.empty or prices_b is None or prices_b.empty:
            logger.warning(f"Missing price data for {pos.stock_a} or {pos.stock_b}. Cannot evaluate exit.")
            return

        current_price_a = prices_a.iloc[-1]
        current_price_b = prices_b.iloc[-1]
        
        # Cointegration/spread recalculation
        common_dates = prices_a.index.intersection(prices_b.index)
        prices_a_aligned = prices_a[common_dates].values
        prices_b_aligned = prices_b[common_dates].values
        spread = prices_a_aligned - pos.hedge_ratio * prices_b_aligned
        
        # Calculate 30-day rolling Z-score
        window = 30
        if len(spread) >= window:
            mean_spread = np.mean(spread[-window:])
            std_spread = np.std(spread[-window:])
            current_z = (spread[-1] - mean_spread) / std_spread if std_spread > 0 else 0.0
        else:
            current_z = 0.0
            
        # Determine exit conditions:
        # 1. Z-score crosses exit threshold (e.g. |Z| < 0.5)
        # 2. Or signal is explicitly 'EXIT'
        should_exit = False
        exit_reason = ""
        
        if sig_match and sig_match['signal'] == 'EXIT':
            should_exit = True
            exit_reason = "Explicit EXIT signal generated."
        elif abs(current_z) < 0.5:
            should_exit = True
            exit_reason = f"Z-score ({current_z:.2f}) reverted inside exit threshold (< 0.5)."
        
        if should_exit:
            # Calculate final P&L
            pnl = pos.shares_a * (current_price_a - pos.entry_price_a) + pos.shares_b * (current_price_b - pos.entry_price_b)
            return_pct = (pnl / self.allocation_per_trade) * 100
            
            # Log to Trade History
            trade_history = VirtualTradeHistory(
                stock_a=pos.stock_a,
                stock_b=pos.stock_b,
                position_type=pos.position_type,
                entry_date=pos.entry_date,
                exit_date=datetime.utcnow(),
                entry_price_a=pos.entry_price_a,
                entry_price_b=pos.entry_price_b,
                exit_price_a=current_price_a,
                exit_price_b=current_price_b,
                shares_a=pos.shares_a,
                shares_b=pos.shares_b,
                pnl=pnl,
                return_pct=return_pct
            )
            
            # Adjust cash: cash = cash + value_at_exit
            portfolio.cash = portfolio.cash + pos.shares_a * current_price_a + pos.shares_b * current_price_b
            
            session.add(trade_history)
            session.delete(pos)
            session.commit()
            
            logger.info(f"CLOSED POSITION: {pos.stock_a}-{pos.stock_b} ({pos.position_type}) | Exit reason: {exit_reason} | PnL: {pnl:,.2f} INR ({return_pct:.2f}%)")

    def _check_and_open_position(self, session: Session, portfolio: VirtualPortfolio, sig: Dict) -> bool:
        """Evaluate if a new signal should trigger a virtual position entry."""
        # Ensure signal type is LONG or SHORT
        if sig['signal'] not in ('LONG', 'SHORT'):
            return False
            
        # Check if already open
        existing = session.query(VirtualPosition).filter(
            ((VirtualPosition.stock_a == sig['stock_a']) & (VirtualPosition.stock_b == sig['stock_b'])) |
            ((VirtualPosition.stock_a == sig['stock_b']) & (VirtualPosition.stock_b == sig['stock_a']))
        ).first()
        
        if existing:
            return False
            
        # Ensure we have enough cash for entry
        if portfolio.cash < self.allocation_per_trade:
            logger.warning(f"Insufficient cash ({portfolio.cash:,.2f} INR) to enter trade for {sig['stock_a']}-{sig['stock_b']} (Required: {self.allocation_per_trade:,.2f} INR).")
            return False
            
        # Get current entry prices
        prices_a = self.data_manager.get_price_series(sig['stock_a'])
        prices_b = self.data_manager.get_price_series(sig['stock_b'])
        
        if prices_a is None or prices_a.empty or prices_b is None or prices_b.empty:
            logger.warning(f"Missing price data for {sig['stock_a']} or {sig['stock_b']}. Skipping entry.")
            return False
            
        price_a = prices_a.iloc[-1]
        price_b = prices_b.iloc[-1]
        
        hedge_ratio = sig.get('hedge_ratio')
        if hedge_ratio is None or np.isnan(hedge_ratio) or hedge_ratio <= 0:
            # Recalculate hedge ratio
            common_dates = prices_a.index.intersection(prices_b.index)
            prices_a_aligned = prices_a[common_dates].values
            prices_b_aligned = prices_b[common_dates].values
            hedge_ratio = self.coint_analyzer.calculate_hedge_ratio(prices_a_aligned, prices_b_aligned)
            if np.isnan(hedge_ratio) or hedge_ratio <= 0:
                logger.warning(f"Invalid hedge ratio ({hedge_ratio}) for {sig['stock_a']}-{sig['stock_b']}. Skipping.")
                return False
                
        # Signed position sizing:
        if sig['signal'] == 'LONG':
            # Buy Stock A, Sell Stock B
            shares_a = self.allocation_per_trade / price_a
            shares_b = -(shares_a * hedge_ratio)
        else: # SHORT signal
            # Sell Stock A, Buy Stock B
            shares_a = -self.allocation_per_trade / price_a
            shares_b = -(shares_a * hedge_ratio) # positive since shares_a is negative
            
        # Update portfolio cash
        portfolio.cash = portfolio.cash - shares_a * price_a - shares_b * price_b
        
        new_pos = VirtualPosition(
            stock_a=sig['stock_a'],
            stock_b=sig['stock_b'],
            position_type=sig['signal'],
            hedge_ratio=hedge_ratio,
            shares_a=shares_a,
            shares_b=shares_b,
            entry_price_a=price_a,
            entry_price_b=price_b,
            entry_z_score=sig.get('z_score_30', sig.get('z_score', np.nan))
        )
        
        session.add(new_pos)
        session.commit()
        
        logger.info(f"ENTERED POSITION: {sig['stock_a']}-{sig['stock_b']} ({sig['signal']}) | Prices: A={price_a:.2f}, B={price_b:.2f} | Shares: A={shares_a:.2f}, B={shares_b:.2f} | Cash Remaining: {portfolio.cash:,.2f} INR")
        return True

_virtual_trader = None

def get_virtual_trader(allocation_per_trade: float = 1000000.0, max_positions: int = 8) -> VirtualTrader:
    """Get or create the global VirtualTrader instance."""
    global _virtual_trader
    if _virtual_trader is None:
        _virtual_trader = VirtualTrader(allocation_per_trade, max_positions)
    return _virtual_trader
