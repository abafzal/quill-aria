"""Core module for ARIA application.

This module contains core utilities including exceptions, logging configuration,
and type definitions.
"""

from .exceptions import *
from .logging_config import setup_logging, get_logger, log_info, log_warning, log_error, log_success
from .types import *

__all__ = [
    # Exceptions
    "AriaBaseException",
    "ConfigurationError", 
    "AuthenticationError",
    "FileProcessingError",
    "UnsupportedFileTypeError",
    "QuestionExtractionError",
    "AnswerGenerationError",
    "DatabricksAPIError",
    "ModelInvocationError",
    "DataValidationError",
    "SessionStateError",
    "ExportError",
    
    # Logging
    "setup_logging",
    "get_logger",
    "log_info",
    "log_warning", 
    "log_error",
    "log_success",
    
    # Types
    "FileType",
    "ProcessingStep",
    "AuthMode",
    "UploadedFile",
    "Question",
    "Answer",
    "QuestionAnswerPair",
    "DocumentMetadata",
    "ProcessingSession",
    "APIRequest",
    "APIResponse",
    "ExportData",
    "TrackingData",
    "DataFrameType",
    "SessionState",
    "ConfigDict",
]
