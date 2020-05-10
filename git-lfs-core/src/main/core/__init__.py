import logging
import os

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
