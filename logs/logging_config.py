# logging_config.py
from pathlib import Path
import logging

LOG_DIR = Path("logs")

#Configures the logging for the system
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            #specifies to write logs only to the app.log file
            logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
        ]
    )