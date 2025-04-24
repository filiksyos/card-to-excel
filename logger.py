import logging
import os
from config import LOG_LEVEL, LOG_FILE

# Ensure the directory for the log file exists
log_dir = os.path.dirname(LOG_FILE)
if log_dir:  # Only create directory if there's a directory path specified
    os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name) 