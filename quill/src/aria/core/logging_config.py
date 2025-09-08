"""Logging configuration for ARIA application.

This module provides centralized logging setup with both console and UI logging
capabilities, following best practices for structured logging.
"""

import logging
import sys
from typing import Optional
from pathlib import Path
import streamlit as st


class StreamlitHandler(logging.Handler):
    """Custom logging handler that can display messages in Streamlit UI."""
    
    def __init__(self, display_in_ui: bool = False) -> None:
        """Initialize the Streamlit handler.
        
        Args:
            display_in_ui: Whether to display log messages in the Streamlit UI
        """
        super().__init__()
        self.display_in_ui = display_in_ui
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Streamlit UI if configured to do so.
        
        Args:
            record: The log record to emit
        """
        if not self.display_in_ui:
            return
            
        msg = self.format(record)
        
        # Display in Streamlit UI based on log level
        if record.levelno >= logging.ERROR:
            st.error(f"❌ {msg}")
        elif record.levelno >= logging.WARNING:
            st.warning(f"⚠️ {msg}")
        elif record.levelno >= logging.INFO:
            st.info(f"📋 {msg}")
        else:  # DEBUG and below
            st.text(f"🔧 {msg}")


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    display_in_ui: bool = False
) -> logging.Logger:
    """Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging output
        display_in_ui: Whether to display logs in Streamlit UI
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("aria")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Streamlit UI handler (if requested)
    if display_in_ui:
        ui_handler = StreamlitHandler(display_in_ui=True)
        ui_handler.setLevel(logging.INFO)
        ui_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(ui_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    payload: dict,
    status_code: Optional[int] = None,
    response: Optional[dict] = None,
    error: Optional[Exception] = None
) -> None:
    """Log API call information with appropriate log level.
    
    Args:
        logger: Logger instance to use
        endpoint: API endpoint that was called
        payload: Request payload (sensitive data will be sanitized)
        status_code: HTTP status code of the response
        response: Response data (optional)
        error: Exception that occurred (optional)
    """
    # Sanitize payload (remove auth tokens)
    sanitized_payload = payload.copy() if isinstance(payload, dict) else {}
    if 'messages' in sanitized_payload:
        # Keep the messages but sanitize any auth info
        pass
    
    # Extract endpoint name for logging
    endpoint_short = endpoint.split('/')[-1] if isinstance(endpoint, str) else 'unknown'
    
    # Log based on success/failure
    if error:
        logger.error(f"API call failed to {endpoint_short}: {error}")
    elif status_code and status_code >= 400:
        logger.error(f"API call failed to {endpoint_short} with status {status_code}")
    else:
        logger.info(f"API call successful to {endpoint_short} with status {status_code}")


def get_logger(name: str = "aria") -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger (typically module name)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience functions for common logging patterns
def log_info(message: str, display_in_ui: bool = False) -> None:
    """Log an info message.
    
    Args:
        message: Message to log
        display_in_ui: Whether to display in Streamlit UI
    """
    logger = get_logger()
    logger.info(message)
    
    if display_in_ui:
        st.info(f"📋 {message}")


def log_warning(message: str, display_in_ui: bool = False) -> None:
    """Log a warning message.
    
    Args:
        message: Message to log
        display_in_ui: Whether to display in Streamlit UI
    """
    logger = get_logger()
    logger.warning(message)
    
    if display_in_ui:
        st.warning(f"⚠️ {message}")


def log_error(message: str, display_in_ui: bool = False) -> None:
    """Log an error message.
    
    Args:
        message: Message to log
        display_in_ui: Whether to display in Streamlit UI
    """
    logger = get_logger()
    logger.error(message)
    
    if display_in_ui:
        st.error(f"❌ {message}")


def log_success(message: str, display_in_ui: bool = False) -> None:
    """Log a success message.
    
    Args:
        message: Message to log
        display_in_ui: Whether to display in Streamlit UI
    """
    logger = get_logger()
    logger.info(f"SUCCESS: {message}")
    
    if display_in_ui:
        st.success(f"✅ {message}") 