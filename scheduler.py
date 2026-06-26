"""
Local scheduler script for the Statistical Arbitrage Platform.
Runs a background loop that executes the pipeline daily at 10:00 AM IST (UTC+5:30).
"""

import sys
import os
import time
from datetime import datetime, timedelta
import logging

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import get_pipeline
from config import UNIVERSE_FILE

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(PROJECT_ROOT, "logs", "scheduler.log"), encoding='utf-8')
    ]
)
logger = logging.getLogger("Scheduler")

TARGET_HOUR = 10
TARGET_MINUTE = 0

def run_scheduler():
    logger.info("=" * 60)
    logger.info("LOCAL PIPELINE SCHEDULER STARTED")
    logger.info(f"Target daily execution time: {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} local time")
    logger.info("=" * 60)
    
    pipeline = get_pipeline()
    
    while True:
        try:
            # Current time
            now = datetime.now()
            
            # Calculate next target datetime
            target_time = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
            
            # If target_time is in the past today, schedule for tomorrow
            if now >= target_time:
                target_time += timedelta(days=1)
                
            seconds_to_wait = (target_time - now).total_seconds()
            
            logger.info(f"Next scheduled run: {target_time.strftime('%Y-%m-%d %H:%M:%S')} (in {seconds_to_wait/3600:.2f} hours)")
            
            # Sleep in intervals of 10 seconds to allow interruptible checking
            while (target_time - datetime.now()).total_seconds() > 0:
                time.sleep(10)
                
            logger.info("Triggering scheduled pipeline execution...")
            result = pipeline.run_full_pipeline(UNIVERSE_FILE)
            logger.info(f"Pipeline executed successfully. Status: {result.get('status')}")
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}", exc_info=True)
            logger.info("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == '__main__':
    run_scheduler()
