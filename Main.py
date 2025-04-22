import time
import logging
import sys
from datetime import datetime
import traceback
import random
from Skimmer import get_permit, notify_error

# Set up logging configuration for the main module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("permit_checker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")


def run_forever() -> None:
    """
    Run the permit checker indefinitely with proper error handling.
    
    This function:
    1. Runs the permit checker in an infinite loop
    2. Handles exceptions properly to prevent crashes
    3. Uses randomized check intervals to avoid detection
    4. Implements longer backoff periods after errors
    5. Sends notifications on errors with cooldown periods
    """
    # Initialize a counter for the number of checks run
    check_count = 0
    
    while True:
        try:
            check_count += 1
            logger.info(f"Starting check #{check_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the permit checker
            get_permit()
            
            # Determine next check interval (random between 40-80 seconds to avoid detection)
            check_interval = random.randint(40, 80)
            
            logger.info(f"Check complete. Next check in {check_interval} seconds")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            # Allow for clean shutdown with Ctrl+C
            logger.info("Program terminated by user")
            sys.exit(0)
        except Exception as e:
            # Catch any unexpected exceptions to keep the program running
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            
            # Send notification with a 30-minute cooldown
            notify_error(e, "Error in main permit checking loop", min_interval_minutes=30)
            
            # Wait a bit longer if we had an error (5-7 minutes)
            error_wait = random.randint(5*60, 7*60)
            logger.info(f"Waiting {error_wait//60} minutes before retrying after error")
            time.sleep(error_wait)


if __name__ == "__main__":
    # Only run if this file is executed directly (not imported)
    logger.info("Starting permit checker service")
    logger.warning("🚨 Main.py has started and is running under supervisor.")

    run_forever()