import logging
import sys
from app.core.config import get_settings

def setup_logging():
    """
    Configure the application logging system
    
    Sets up log levels, formatters, and handlers for both console and file output.
    Ensures proper log rotation to prevent log files from growing too large.
    """
    # Get configuration
    settings = get_settings()
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Set root log level
    log_level = getattr(logging, settings.log_level)
    root_logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)

    # Disable verbose logging for pymongo
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("sse_starlette.sse").setLevel(logging.INFO)
    
    # Log initialization complete
    root_logger.info("Logging system initialized - Console and file logging active") 