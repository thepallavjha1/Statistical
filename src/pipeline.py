"""
Main pipeline orchestrator for the Statistical Arbitrage Platform.
"""

import sys
import os

# Allow `python src/pipeline.py` from project root (local + GitHub Actions)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional

from src.data_ingestion import get_data_manager
from src.pair_selection import get_pair_selection_engine
from src.cointegration import get_cointegration_analyzer
from src.signal_engine import get_signal_engine
from src.backtesting import get_backtest_engine
from src.database import get_db_ops
from src.utils import OpportunityRanker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatArbPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.data_manager = get_data_manager()
        self.pair_engine = get_pair_selection_engine()
        self.coint_analyzer = get_cointegration_analyzer()
        self.signal_engine = get_signal_engine()
        self.backtest_engine = get_backtest_engine()
        self.db_ops = get_db_ops()
    
    def run_full_pipeline(self, universe_file: str) -> Dict:
        """Run the full analysis pipeline."""
        
        try:
            logger.info("=" * 60)
            logger.info("STARTING STATISTICAL ARBITRAGE PIPELINE")
            logger.info(f"Timestamp: {datetime.utcnow()}")
            logger.info("=" * 60)
            
            # Step 1: Load and update data
            logger.info("\n[STEP 1] Loading and updating data...")
            symbols = self.data_manager.load_universe(universe_file)
            self._sync_universe_stocks(universe_file, symbols)
            for i, symbol in enumerate(symbols):
                self.data_manager.update_stock_data(symbol)
                if i % 25 == 0 and i > 0:
                    logger.info(f"Downloaded {i}/{len(symbols)} stocks...")
                time.sleep(0.1)
            
            logger.info(f"Updated {len(symbols)} stocks")
            
            # Step 2: Filter by liquidity
            logger.info("\n[STEP 2] Filtering by liquidity...")
            liquid_symbols = self.pair_engine.filter_by_liquidity(symbols, min_avg_volume=1e6)
            logger.info(f"Passed liquidity filter: {len(liquid_symbols)}/{len(symbols)}")
            
            # Step 3: Find correlated pairs
            logger.info("\n[STEP 3] Finding correlated pairs...")
            pairs = self.pair_engine.find_correlated_pairs(liquid_symbols, lookback_days=252)
            logger.info(f"Found {len(pairs)} correlated pairs")
            
            # Step 4: Test cointegration
            logger.info("\n[STEP 4] Testing cointegration...")
            cointegrated_pairs = self.coint_analyzer.test_pairs_batch(pairs)
            logger.info(f"Found {len(cointegrated_pairs)} cointegrated pairs")
            
            # Step 5: Generate signals
            logger.info("\n[STEP 5] Generating signals...")
            signals = self.signal_engine.generate_signals_batch(cointegrated_pairs)
            logger.info(f"Generated {len(signals)} active signals")
            
            # Step 6: Rank opportunities
            logger.info("\n[STEP 6] Ranking opportunities...")
            ranked_signals = OpportunityRanker.rank_opportunities(signals)
            top_opportunities = ranked_signals[:20]
            logger.info(f"Top 20 opportunities identified")
            
            # Step 7: Store results
            logger.info("\n[STEP 7] Storing results in database...")
            for pair in cointegrated_pairs:
                self.db_ops.add_cointegration(
                    pair['stock_a'], pair['stock_b'],
                    pair['test_statistic'], pair['p_value'],
                    str(pair['critical_values']),
                    pair.get('hedge_ratio')
                )
            
            for signal in signals:
                self.db_ops.add_signal(
                    signal['stock_a'], signal['stock_b'],
                    signal['signal'],
                    signal['z_score_30'], signal['z_score_60'], signal['z_score_90'],
                    signal['current_spread'], signal['signal_strength']
                )
            
            logger.info(f"Stored {len(cointegrated_pairs)} cointegration results")
            logger.info(f"Stored {len(signals)} signals")
            
            # Step 8: Execute Virtual Paper Trading
            try:
                from src.virtual_trading.executor import get_virtual_trader
                logger.info("\n[STEP 8] Executing Virtual Paper Trading...")
                virtual_trader = get_virtual_trader()
                virtual_trader.execute_trading_round(signals)
            except Exception as vt_err:
                logger.error(f"Virtual trading execution failed: {str(vt_err)}", exc_info=True)
            
            # Create summary
            summary = {
                'timestamp': datetime.utcnow(),
                'universe_size': len(symbols),
                'liquid_stocks': len(liquid_symbols),
                'correlated_pairs': len(pairs),
                'cointegrated_pairs': len(cointegrated_pairs),
                'active_signals': len(signals),
                'top_opportunities': top_opportunities,
                'status': 'SUCCESS'
            }
            
            logger.info("\n" + "=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Stocks: {len(symbols)} → Liquid: {len(liquid_symbols)}")
            logger.info(f"Pairs: {len(pairs)} → Cointegrated: {len(cointegrated_pairs)}")
            logger.info(f"Active Signals: {len(signals)}")
            logger.info("=" * 60 + "\n")
            
            return summary
        
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            return {'status': 'FAILED', 'error': str(e)}
    
    def get_latest_signals(self, top_n: int = 20) -> List[Dict]:
        """Get latest signals from database."""
        signals = self.db_ops.get_latest_signals(hours=24)
        signals_list = [
            {
                'stock_a': s.stock_a,
                'stock_b': s.stock_b,
                'signal': s.signal_type,
                'z_score': s.z_score_30,
                'spread': s.current_spread,
                'strength': s.signal_strength
            }
            for s in signals
        ]
        return signals_list[:top_n]
    
    def get_cointegrated_pairs(self, limit: int = 100) -> List[Dict]:
        """Get cointegrated pairs from database."""
        pairs = self.db_ops.get_cointegrated_pairs(threshold=0.05)
        pairs_list = [
            {
                'stock_a': p.stock_a,
                'stock_b': p.stock_b,
                'p_value': p.p_value,
                'test_statistic': p.test_statistic,
                'hedge_ratio': p.hedge_ratio,
                'date': p.test_date
            }
            for p in pairs
        ]
        return pairs_list[:limit]

    def _sync_universe_stocks(self, universe_file: str, symbols: List[str]):
        """Register universe stocks in the database."""
        import pandas as pd
        try:
            from config import STOCK_UNIVERSE
        except ImportError:
            STOCK_UNIVERSE = "NIFTY500"

        try:
            universe_df = pd.read_csv(universe_file)
            meta = {
                row['symbol']: row
                for _, row in universe_df.iterrows()
                if pd.notna(row.get('symbol'))
            }
        except Exception:
            meta = {}

        for symbol in symbols:
            if self.db_ops.get_stock(symbol):
                continue
            row = meta.get(symbol)
            company_name = row['company_name'] if row is not None and 'company_name' in row else None
            sector = row['sector'] if row is not None and 'sector' in row else None
            self.db_ops.add_stock(symbol, company_name, sector, STOCK_UNIVERSE)


# Global instance
_pipeline = None


def get_pipeline() -> StatArbPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = StatArbPipeline()
    return _pipeline


if __name__ == '__main__':
    try:
        from config import UNIVERSE_FILE
        universe_file = UNIVERSE_FILE
    except ImportError:
        import os
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        universe_file = os.path.join(config_dir, 'nifty500.csv')
    
    # Run pipeline
    pipeline = get_pipeline()
    result = pipeline.run_full_pipeline(universe_file)
    
    print(f"\nPipeline Result: {result['status']}")
    if result['status'] == 'SUCCESS':
        print(f"Cointegrated Pairs: {result['cointegrated_pairs']}")
        print(f"Active Signals: {result['active_signals']}")
