# logging_config.py
import logging

def configure_logger():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)