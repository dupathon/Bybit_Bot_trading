import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from crypto_bot.config import Config

def setup_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Rotating File Handler (max 10MB per file, keep 5 backup files)
    try:
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        fh = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5  # Keep 5 old log files
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")
        
    return logger
