"""
Logging configuration for the auto documentation generator.

This module sets up structured logging with appropriate formatters
and handlers based on configuration.
"""

import logging
import logging.handlers
import sys
from typing import Dict, Any, Optional
from pathlib import Path


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up logging configuration.
    
    Args:
        config: Configuration dictionary containing logging settings
    """
    logging_config = config.get('logging', {})
    
    # Get logging parameters
    level = logging_config.get('level', 'INFO').upper()
    format_str = logging_config.get('format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = logging_config.get('file')
    console_enabled = logging_config.get('console', True)
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler if enabled
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Warning: Failed to set up file logging: {e}")
    
    # Set up specific logger levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Suppress OpenAI client internal logging
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('openai._base_client').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
