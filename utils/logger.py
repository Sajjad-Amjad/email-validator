import logging
import sys
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE

def setup_logger(name="email_validator"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger

def log_progress(processed, total, status="Processing"):
    percentage = (processed / total) * 100 if total > 0 else 0
    print(f"\r{status}: {processed}/{total} ({percentage:.1f}%)", end="", flush=True)