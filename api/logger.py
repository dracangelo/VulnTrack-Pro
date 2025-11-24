import logging
import sys
from flask.logging import default_handler

def configure_logging(app):
    app.logger.removeHandler(default_handler)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Also configure root logger for other libraries
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
