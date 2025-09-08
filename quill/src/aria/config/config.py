"""Unified configuration system for ARIA application.

This module provides centralized configuration management with environment variable
loading, validation, type safety, and domain-specific settings all in one place.
"""

import os
from typing import Optional, Final, Any
from pydantic import BaseModel, field_validator, Field
from pydantic_settings import BaseSettings
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from dotenv import load_dotenv

# Load environment variables from .env file only in local development
# In Databricks Apps, all environment variables are provided automatically
if not os.getenv('DATABRICKS_CLIENT_ID'):
    # Only load .env if we're not in a Databricks Apps environment
    load_dotenv()


# =============================================================================
# CUSTOMIZABLE SETTINGS - EDIT THESE VALUES TO CONFIGURE YOUR DEPLOYMENT
# =============================================================================
# 
# To customize ARIA for your deployment, simply edit the values below.
# These settings control the core behavior of the application:
#
# 1. DATABRICKS_HOST: Your Databricks workspace URL
# 2. ANSWER_GENERATION_MODEL: The model used to generate answers
# 3. QUESTION_EXTRACTION_SYSTEM_PROMPT: How the AI extracts questions
# 4. ANSWER_GENERATION_SYSTEM_PROMPT: How the AI generates answers
#
# All other settings in this file reference these constants.
# =============================================================================

# Databricks Configuration
DATABRICKS_HOST = "http://e2-demo-field-eng.cloud.databricks.com"
DATABRICKS_VOLUME_PATH = "/Volumes/main/default/app_files"

# Model Configuration
QUESTION_EXTRACTION_MODEL = "databricks-claude-3-7-sonnet"
ANSWER_GENERATION_MODEL = "agents_users-afsana_afzal-mbo_demo"

# Application Branding
APP_TITLE = "Quill - Financial Services Intelligent Assistant"
APP_DESCRIPTION = "AI-powered tool for regulatory compliance and reporting"
DOMAIN_NAME = "Financial Services"
DOMAIN_DESCRIPTION = "Intelligent Assistant for Financial Services"

# Question Extraction System Prompt (used by AI service)
QUESTION_EXTRACTION_SYSTEM_PROMPT = """You are an expert assistant for rewriting complex forms into structured, numbered questions.
Your task is to convert a set of interrelated subquestions into clearly numbered and grouped questions 
using hierarchical numbering (e.g., 1.0, 1.1) and topic-based organization.

Step 1: Thematic Categorization
Before rewriting, analyze the set of subquestions and identify logical groupings. Categorize each sub-question into 
the most appropriate group. Use context clues and key phrases to determine what the question is about. 
If a question starts discussing a new category, always start a new topic.

Step 2: Structured Rewriting
Once categorized, rewrite the questions following these rules:
1. Each category becomes a new numbered section.
2. Number the questions in order:
   • 1: Main question, often preceded by a number 
   • 1.1, 1.2, 1.3, etc.: Follow-up questions 
3. Disambiguate vague references: Replace pronouns like "this" or "it" with clear references to the capability.
   • ❌ "Do we have derivatives exposures?"
   • ✅ "Do we have derivatives exposures (OTC or exchange-traded) requiring transaction and counterparty reporting under EMIR (EU)?"
4. Preserve the original intent and detail of each question. Only rewrite to clarify or resolve ambiguity.
5. If the question expects a specific type of answer (e.g., "Options:", "max 500 characters"), include
   that instruction at the end of the question.
6. Any answer options listed after the question should be included as part of the question.
7. OUTPUT ONLY valid JSON. No extra text, no markdown, no preambles, no explanations.
8. IMPORTANT: 
   - ONLY extract questions that actually exist in the provided document
   - If no questions are found, return an empty JSON array: []
   - NEVER invent or hallucinate questions that aren't in the original text
   - Do not use the example above as a template for content, only for format
9. Example output structure:
[
  {
    "question": "1",
    "sub_topics": [
      {
        "topic": "Synthetic Data Generation",
        "sub_questions": [
          {
            "sub_question": "1.01",
            "text": "Does your platform support synthetic data generation?"
          },
          {
            "sub_question": "1.02",
            "text": "How is synthetic data generation supported in your platform?"
          },
          {
            "sub_question": "1.03",
            "text": "Please provide any further detail on how synthetic data generation is supported. (Maximum 1000 characters)"
          }
        ]
      },
      {
        "topic": "AI-Based Recommendation",
        "sub_questions": [
          {
            "sub_question": "1.04",
            "text": "Does your platform support AI-based recommendations?"
          },
          {
            "sub_question": "1.05",
            "text": "How are AI-based recommendations supported in your platform?"
          },
          {
            "sub_question": "1.06",
            "text": "Please provide any further detail on how AI-based recommendations are supported. (Maximum 1000 characters)"
          }
        ]
      }
    ]
  },
  {
    "question": "2",
    "sub_topics": [
      {
        "topic": "Data Augmentation",
        "sub_questions": [
          {
            "sub_question": "2.01",
            "text": "Does your platform support data augmentation?"
          },
          {
            "sub_question": "2.02",
            "text": "How is data augmentation supported in your platform?"
          },
          {
            "sub_question": "2.03",
            "text": "Please provide any further detail on how data augmentation is supported. (Maximum 1000 characters)"
          }
        ]
      }
    ]
  }
]"""

# Answer Generation System Prompt (used by AI service)
ANSWER_GENERATION_SYSTEM_PROMPT = """
You are an AI assistant expert on regulatory requirements and reporting for 
financial institutions. 

Your task is to generate informative, concise, and accurate responses to  questions about
regulatory requirements.

Follow these specific guidelines:
- Focus on providing direct answers based only on the information provided.
- Use confident, professional language focusing on strengths without overselling
- Be truthful and accurate about our capabilities
- Use clear, structured responses with bullet points where appropriate
- Format using Markdown for clear structure"""

# Default Custom Prompt for Answer Generation
DEFAULT_CUSTOM_PROMPT = """If a question doesn't ask how or for details, answer in 
one sentence. If a question includes options, answer by selecting an option."""

# =============================================================================
# DOMAIN-SPECIFIC CONFIGURATION
# =============================================================================

class DomainConfig:
    """Domain-specific configuration for the application."""
    
    # Domain identity
    domain_name: str = DOMAIN_NAME
    domain_description: str = DOMAIN_DESCRIPTION
    
    # Application branding
    app_title: str = APP_TITLE
    app_description: str = APP_DESCRIPTION
    
    # File processing
    supported_file_types: list[str] = [".csv", ".html", ".htm"]
    supported_extensions: set[str] = {".csv", ".html", ".htm"}
    max_file_size_mb: int = 50
    max_questions_per_batch: int = 20
    
    # Export formats
    export_extensions: dict[str, str] = {
        "csv": ".csv",
        "excel": ".xlsx",
        "json": ".json"
    }
    
    # MIME types
    mime_types: dict[str, str] = {
        ".csv": "text/csv",
        ".html": "text/html",
        ".htm": "text/html",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".json": "application/json"
    }
    
    # Model configuration
    models: dict[str, str] = {
        "question_extraction": QUESTION_EXTRACTION_MODEL,
        "answer_generation": ANSWER_GENERATION_MODEL
    }
    
    # Available models for UI selection
    available_models: dict[str, str] = {
        "Claude 3.5 Sonnet": "databricks-claude-3-5-sonnet",
        "Claude 3 Sonnet": "databricks-claude-3-sonnet",
        "Claude 3 Haiku": "databricks-claude-3-haiku",
        "Claude 3.7 Sonnet": "databricks-claude-3-7-sonnet"
    }
    
    default_extraction_model: str = QUESTION_EXTRACTION_MODEL
    
    # Databricks configuration
    databricks: dict[str, str] = {
        "host": DATABRICKS_HOST,
        "volume_path": DATABRICKS_VOLUME_PATH
    }
    
    # API configuration
    api: dict[str, Any] = {
        "default_timeout_seconds": 300,
        "max_retries": 3,
        "retry_wait_seconds": 5,
        "default_max_tokens": 4000,
        "default_temperature": 0.1,
        "batch_max_tokens": 8000
    }
    
    # UI constants
    ui_constants: dict[str, int] = {
        "sidebar_width": 300,
        "preview_height": 400,
        "grid_height": 600
    }
    
    # Regex patterns
    regex_patterns: dict[str, str] = {
        "question_id_pattern": r"Q(\d+):",
        "fallback_question_pattern": r"(\d+)\."
    }
    
    # Session state keys
    session_keys: dict[str, str] = {
        "current_step": "current_step",
        "document_name": "document_name",
        "uploaded_file": "uploaded_file",
        "file_path": "file_path",
        "processed_file_path": "processed_file_path",
        "questions": "questions",
        "answers": "answers",
        "extraction_model": "extraction_model",
        "file_preview": "file_preview",
        "custom_extraction_prompt": "custom_extraction_prompt",
        "custom_prompt": "custom_prompt",
        "TEMP_DIR": "temp_dir",
        "STEP": "current_step",
        "RFI_NAME": "document_name",
        "UPLOADED_FILE": "uploaded_file",
        "UPLOADED_FILE_PATH": "file_path",
        "TEMP_UPLOADED_FILE_PATH": "temp_uploaded_file_path",
        "QUESTIONS": "questions",
        "OTHER_DATA": "other_data",
        "DF_INPUT": "df_input",
        "EXTRACTION_COMPLETE": "extraction_complete",
        "EXTRACTION_IN_PROGRESS": "extraction_in_progress",
        "GENERATION_IN_PROGRESS": "generation_in_progress",
        "GENERATED_ANSWERS": "generated_answers",
        "GENERATED_ANSWERS_DF": "generated_answers_df",
        "GENERATION_COMPLETE": "generation_complete",
        "SELECTED_QUESTIONS": "selected_questions",
        "EXPORT_ANSWERS_DF": "export_answers_df",
        "OUTPUT_PATH": "output_path",
        "OUTPUT_FILE_NAME": "output_file_name",
        "CURRENT_PREVIEW_FILE": "current_preview_file",
        "EXECUTION_TIME": "execution_time",
        "SELECTED_EXTRACTION_MODEL": "selected_extraction_model"
    }
    
    # Error messages
    error_messages: dict[str, str] = {
        "UNSUPPORTED_FILE_TYPE": "Unsupported file type: {file_type}. Please upload a CSV or HTML file.",
        "FILE_TOO_LARGE": "File size exceeds maximum allowed size of {max_size}MB.",
        "EXTRACTION_FAILED": "Failed to extract questions from the document.",
        "GENERATION_FAILED": "Failed to generate answers for the questions.",
        "INVALID_DOCUMENT": "Invalid document format or content.",
        "NETWORK_ERROR": "Network error occurred. Please check your connection and try again.",
        "AUTH_ERROR": "Authentication failed. Please check your credentials.",
        "TIMEOUT_ERROR": "Request timed out. Please try again.",
        "GENERIC_ERROR": "An unexpected error occurred: {error}",
        "NO_ANSWERS_AVAILABLE": "No answers have been generated yet. Please complete the previous steps first.",
        "NO_FILE_UPLOADED": "No file has been uploaded yet. Please upload a file in Step 1 first.",
        "NO_QUESTIONS_AVAILABLE": "No questions have been extracted yet. Please complete Step 2 first."
    }
    
    # Success messages
    success_messages: dict[str, str] = {
        "UPLOAD_SUCCESS": "File uploaded successfully!",
        "EXTRACTION_SUCCESS": "Questions extracted successfully!",
        "QUESTIONS_EXTRACTED": "Successfully extracted {count} questions from the document!",
        "GENERATION_SUCCESS": "Answers generated successfully!",
        "ANSWERS_GENERATED": "Successfully generated {count} answers!",
        "DOWNLOAD_SUCCESS": "File downloaded successfully!",
        "PROCESSING_COMPLETE": "Processing completed successfully!"
    }
    
    # CSS classes
    css_classes: dict[str, str] = {
        "step_container": "step-container",
        "step_header": "step-header",
        "step_content": "step-content",
        "success_message": "success-message",
        "error_message": "error-message",
        "warning_message": "warning-message"
    }
    
    # Column mappings for different data formats
    column_mappings: dict[str, dict[str, str]] = {
        "csv": {
            "question": "Question",
            "answer": "Answer",
            "id": "ID"
        },
        "excel": {
            "question": "Question",
            "answer": "Answer",
            "id": "ID"
        }
    }
    
    # AgGrid configuration
    aggrid_config: dict[str, Any] = {
        "theme": "streamlit",
        "height": 400,
        "fit_columns_on_grid_load": True,
        "selection_mode": "multiple",
        "use_checkbox": True
    }
    

    
    # System prompt for question extraction (used by AI service)
    extraction_system_prompt: str = QUESTION_EXTRACTION_SYSTEM_PROMPT
    
    # System prompt for answer generation (used by AI service)
    generation_system_prompt: str = ANSWER_GENERATION_SYSTEM_PROMPT
    
    # Default custom prompt for answer generation
    default_custom_prompt: str = DEFAULT_CUSTOM_PROMPT
    



# Create domain config instance
domain_config = DomainConfig()


# =============================================================================
# SETTINGS CLASSES WITH ENVIRONMENT VARIABLE SUPPORT
# =============================================================================

class DatabricksSettings(BaseSettings):
    """Databricks-specific configuration settings using unified authentication."""
    
    host: str = Field(default=domain_config.databricks["host"], description="Databricks workspace host URL")
    volume_path: str = Field(default=domain_config.databricks["volume_path"], description="Volume path for file storage")
    
    class Config:
        env_prefix = "DATABRICKS_"
        case_sensitive = False
    
    @field_validator("host")
    @classmethod
    def normalize_host_url(cls, v: str) -> str:
        """Ensure the host URL has the proper https:// prefix."""
        if not v:
            raise ValueError("Databricks host URL is required")
        
        if not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v
    
    def get_model_endpoint_url(self, model_name: str) -> str:
        """Construct the full endpoint URL for a given model name."""
        return f"{self.host}/serving-endpoints/{model_name}/invocations"


class ModelSettings(BaseSettings):
    """AI model configuration settings."""
    
    question_extraction_model: str = Field(
        default=domain_config.models["question_extraction"],
        description="Model name for question extraction"
    )
    answer_generation_model: str = Field(
        default=domain_config.models["answer_generation"],
        description="Model name for answer generation"
    )
    
    class Config:
        env_prefix = ""
        case_sensitive = False


class TrackingSettings(BaseSettings):
    """Usage tracking configuration."""
    
    volume_path: str = Field(
        default="/Volumes/main/default/tracking",
        description="Volume path for tracking data"
    )
    enabled: bool = Field(default=True, description="Enable usage tracking")
    
    class Config:
        env_prefix = "TRACKING_"
        case_sensitive = False


class AppSettings(BaseSettings):
    """Main application configuration."""
    
    debug: bool = Field(default=False, description="Enable debug mode")
    development_mode: bool = Field(default=False, description="Enable development mode (relaxed validation)")
    max_file_size_mb: int = Field(default=domain_config.max_file_size_mb, description="Maximum file upload size in MB")
    session_timeout_hours: int = Field(default=24, description="Session timeout in hours")
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False


# =============================================================================
# UNIFIED CONFIGURATION CLASS
# =============================================================================

class AppConfig:
    """Unified configuration class that combines all settings and constants."""
    
    def __init__(self):
        """Initialize all configuration sections."""
        # Settings with environment variable support
        self.databricks = DatabricksSettings()
        self.models = ModelSettings()
        self.tracking = TrackingSettings()
        self.app = AppSettings()
        
        # Domain-specific constants (read-only)
        self.domain = domain_config
        
        # Computed properties
        self.question_extraction_endpoint = self.databricks.get_model_endpoint_url(
            self.models.question_extraction_model
        )
        self.answer_generation_endpoint = self.databricks.get_model_endpoint_url(
            self.models.answer_generation_model
        )
    
    # =============================================================================
    # CONSTANTS (for backward compatibility)
    # =============================================================================
    
    @property
    def SUPPORTED_FILE_TYPES(self) -> list[str]:
        """Supported file types."""
        return domain_config.supported_file_types
    
    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        """Maximum file size in MB."""
        return domain_config.max_file_size_mb
    
    @property
    def MAX_QUESTIONS_PER_BATCH(self) -> int:
        """Maximum questions per batch."""
        return domain_config.max_questions_per_batch
    
    @property
    def AVAILABLE_CLAUDE_MODELS(self) -> dict[str, str]:
        """Available Claude models."""
        return domain_config.available_models
    
    @property
    def DEFAULT_QUESTION_EXTRACTION_MODEL(self) -> str:
        """Default question extraction model."""
        return domain_config.default_extraction_model
    
    @property
    def DEFAULT_TIMEOUT_SECONDS(self) -> int:
        """Default timeout in seconds."""
        return domain_config.api["default_timeout_seconds"]
    
    @property
    def MAX_RETRIES(self) -> int:
        """Maximum retries."""
        return domain_config.api["max_retries"]
    
    @property
    def RETRY_WAIT_SECONDS(self) -> int:
        """Retry wait seconds."""
        return domain_config.api["retry_wait_seconds"]
    
    @property
    def SIDEBAR_WIDTH(self) -> int:
        """Sidebar width."""
        return domain_config.ui_constants["sidebar_width"]
    
    @property
    def PREVIEW_HEIGHT(self) -> int:
        """Preview height."""
        return domain_config.ui_constants["preview_height"]
    
    @property
    def GRID_HEIGHT(self) -> int:
        """Grid height."""
        return domain_config.ui_constants["grid_height"]
    
    @property
    def DEFAULT_MAX_TOKENS(self) -> int:
        """Default max tokens."""
        return domain_config.api["default_max_tokens"]
    
    @property
    def DEFAULT_TEMPERATURE(self) -> float:
        """Default temperature."""
        return domain_config.api["default_temperature"]
    
    @property
    def BATCH_MAX_TOKENS(self) -> int:
        """Batch max tokens."""
        return domain_config.api["batch_max_tokens"]
    
    @property
    def QUESTION_ID_PATTERN(self) -> str:
        """Question ID pattern."""
        return domain_config.regex_patterns["question_id_pattern"]
    
    @property
    def FALLBACK_QUESTION_PATTERN(self) -> str:
        """Fallback question pattern."""
        return domain_config.regex_patterns["fallback_question_pattern"]
    

    
    @property
    def EXTRACTION_SYSTEM_PROMPT(self) -> str:
        """System prompt for question extraction."""
        return domain_config.extraction_system_prompt
    
    @property
    def GENERATION_SYSTEM_PROMPT(self) -> str:
        """System prompt for answer generation."""
        return domain_config.generation_system_prompt
    
    @property
    def DEFAULT_CUSTOM_PROMPT(self) -> str:
        """Default custom prompt for answer generation."""
        return domain_config.default_custom_prompt
    
    @property
    def SESSION_KEYS(self) -> dict[str, str]:
        """Session keys."""
        return domain_config.session_keys
    
    @property
    def ERROR_MESSAGES(self) -> dict[str, str]:
        """Error messages."""
        return domain_config.error_messages
    
    @property
    def SUCCESS_MESSAGES(self) -> dict[str, str]:
        """Success messages."""
        return domain_config.success_messages
    
    @property
    def CSS_CLASSES(self) -> dict[str, str]:
        """CSS classes."""
        return domain_config.css_classes
    
    @property
    def SUPPORTED_EXTENSIONS(self) -> set[str]:
        """Supported extensions."""
        return domain_config.supported_extensions
    
    @property
    def EXPORT_EXTENSIONS(self) -> dict[str, str]:
        """Export extensions."""
        return domain_config.export_extensions
    
    @property
    def MIME_TYPES(self) -> dict[str, str]:
        """MIME types."""
        return domain_config.mime_types
    
    @property
    def COLUMN_MAPPINGS(self) -> dict[str, dict[str, str]]:
        """Column mappings."""
        return domain_config.column_mappings
    
    @property
    def AGGRID_CONFIG(self) -> dict[str, Any]:
        """AgGrid configuration."""
        return domain_config.aggrid_config
    
    # =============================================================================
    # DATABRICKS INTEGRATION
    # =============================================================================
    
    def get_workspace_client(self) -> Optional[WorkspaceClient]:
        """Create a Databricks WorkspaceClient using unified authentication.
        
        The SDK automatically detects the best authentication method from environment variables.
        
        Returns:
            WorkspaceClient instance or None if configuration fails
        """
        try:
            # Simply create the client - SDK handles all authentication automatically
            client = WorkspaceClient()
            return client
        except Exception as e:
            print(f"[Config Error] Failed to create WorkspaceClient: {e}")
            return None
    
    def get_auth_headers(self) -> Optional[dict[str, str]]:
        """Get authentication headers for direct API calls.
        
        Returns:
            Dictionary with authorization headers or None if not available
        """
        try:
            workspace_client = self.get_workspace_client()
            if workspace_client is None:
                return None
            
            # Use the SDK's authentication mechanism
            # Try multiple approaches based on the actual SDK behavior
            
            # Method 1: Try to get auth headers directly from the config
            try:
                auth_provider = workspace_client.config.authenticate()
                
                # Check if auth_provider is already a dict (some auth methods return headers directly)
                if isinstance(auth_provider, dict) and 'Authorization' in auth_provider:
                    return {
                        'Authorization': auth_provider['Authorization'],
                        'Content-Type': 'application/json'
                    }
                
                # If it's callable, try to call it with a dummy request
                elif callable(auth_provider):
                    import requests
                    dummy_request = requests.Request('GET', f"{self.databricks.host}/api/2.0/clusters/list")
                    authenticated_request = auth_provider(dummy_request)
                    
                    if authenticated_request.headers and 'Authorization' in authenticated_request.headers:
                        return {
                            'Authorization': authenticated_request.headers['Authorization'],
                            'Content-Type': 'application/json'
                        }
                
            except Exception:
                pass
            
            # Method 2: Fallback to direct token access for PAT authentication
            try:
                if hasattr(workspace_client.config, 'token') and workspace_client.config.token:
                    return {
                        'Authorization': f'Bearer {workspace_client.config.token}',
                        'Content-Type': 'application/json'
                    }
            except Exception:
                pass
            
            return None
        except Exception:
            return None
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """Validate the current configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        critical_errors = []
        warnings = []
        
        # In development mode, be more permissive with validation
        if self.app.development_mode:
            warnings.append("Running in development mode - minimal validation applied")
            
            # Only check absolute essentials for development
            if not self.databricks.host:
                critical_errors.append("DATABRICKS_HOST is required")
            
            # Everything else becomes a warning in dev mode
            try:
                test_client = self.get_workspace_client()
                if test_client is None:
                    warnings.append("No authentication configured - API calls will fail")
            except Exception:
                warnings.append("Authentication configuration issue - API calls may fail")
                
        else:
            # Normal validation for production
            # Check Databricks configuration - CRITICAL ERRORS
            if not self.databricks.host:
                critical_errors.append("DATABRICKS_HOST is required")
            
            # Test if authentication is available
            try:
                test_client = self.get_workspace_client()
                if test_client is None:
                    critical_errors.append("No valid Databricks authentication found")
            except Exception:
                critical_errors.append("Databricks authentication configuration error")
            
            # Check model configuration - CRITICAL ERRORS
            if not self.models.question_extraction_model:
                critical_errors.append("Question extraction model name is required")
            
            if not self.models.answer_generation_model:
                critical_errors.append("Answer generation model name is required")
        
        # Return True if no critical errors, False if there are critical errors
        # Warnings are logged but don't prevent the app from starting
        all_issues = critical_errors + warnings
        return len(critical_errors) == 0, all_issues
    
    def log_configuration(self) -> None:
        """Log current configuration (without sensitive data)."""
        print(f"[Config] Domain: {domain_config.domain_name} - {domain_config.domain_description}")
        print(f"[Config] Databricks Host: {self.databricks.host}")
        
        # Determine auth mode from environment variables
        auth_mode = "Unknown"
        if os.getenv('DATABRICKS_CLIENT_ID'):
            auth_mode = "Service Principal"
        elif os.getenv('DATABRICKS_TOKEN'):
            auth_mode = "Personal Access Token"
        
        print(f"[Config] Auth Mode: {auth_mode}")
        print(f"[Config] Question Extraction Model: {self.models.question_extraction_model}")
        print(f"[Config] Answer Generation Model: {self.models.answer_generation_model}")
        print(f"[Config] Debug Mode: {self.app.debug}")
        print(f"[Config] Development Mode: {self.app.development_mode}")
        
        # Additional debug info for authentication troubleshooting
        if self.app.debug:
            print(f"[Config Debug] Environment Variables Present:")
            env_vars = ['DATABRICKS_HOST', 'DATABRICKS_TOKEN', 'DATABRICKS_CLIENT_ID', 'DATABRICKS_CLIENT_SECRET', 'APP_DEVELOPMENT_MODE']
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    display_value = "***" if any(secret in var for secret in ['TOKEN', 'SECRET']) else value
                    print(f"[Config Debug]   {var}: {display_value}")
                else:
                    print(f"[Config Debug]   {var}: Not Set")
        
        is_valid, issues = self.validate_configuration()
        if issues:
            # Separate critical errors from warnings
            critical_errors = []
            warnings = []
            
            for issue in issues:
                if issue.startswith("Running in development"):
                    warnings.append(issue)
                else:
                    critical_errors.append(issue)
            
            if critical_errors:
                print("[Config Errors]:")
                for error in critical_errors:
                    print(f"  - {error}")
            
            if warnings:
                print("[Config Warnings]:")
                for warning in warnings:
                    print(f"  - {warning}")


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

# Create unified config instance
config = AppConfig()

# Create backward compatibility aliases
settings = config  # For code that imports 'settings'

# Constants for backward compatibility (can be imported directly)
SUPPORTED_FILE_TYPES: Final[list[str]] = config.SUPPORTED_FILE_TYPES
MAX_FILE_SIZE_MB: Final[int] = config.MAX_FILE_SIZE_MB
MAX_QUESTIONS_PER_BATCH: Final[int] = config.MAX_QUESTIONS_PER_BATCH
AVAILABLE_CLAUDE_MODELS: Final[dict[str, str]] = config.AVAILABLE_CLAUDE_MODELS
DEFAULT_QUESTION_EXTRACTION_MODEL: Final[str] = config.DEFAULT_QUESTION_EXTRACTION_MODEL
DEFAULT_TIMEOUT_SECONDS: Final[int] = config.DEFAULT_TIMEOUT_SECONDS
MAX_RETRIES: Final[int] = config.MAX_RETRIES
RETRY_WAIT_SECONDS: Final[int] = config.RETRY_WAIT_SECONDS
SIDEBAR_WIDTH: Final[int] = config.SIDEBAR_WIDTH
PREVIEW_HEIGHT: Final[int] = config.PREVIEW_HEIGHT
GRID_HEIGHT: Final[int] = config.GRID_HEIGHT
DEFAULT_MAX_TOKENS: Final[int] = config.DEFAULT_MAX_TOKENS
DEFAULT_TEMPERATURE: Final[float] = config.DEFAULT_TEMPERATURE
BATCH_MAX_TOKENS: Final[int] = config.BATCH_MAX_TOKENS
QUESTION_ID_PATTERN: Final[str] = config.QUESTION_ID_PATTERN
FALLBACK_QUESTION_PATTERN: Final[str] = config.FALLBACK_QUESTION_PATTERN

# EXTRACTION_SYSTEM_PROMPT: Final[str] = config.EXTRACTION_SYSTEM_PROMPT
# GENERATION_SYSTEM_PROMPT: Final[str] = config.GENERATION_SYSTEM_PROMPT
# DEFAULT_CUSTOM_PROMPT: Final[str] = config.DEFAULT_CUSTOM_PROMPT
SESSION_KEYS: Final[dict[str, str]] = config.SESSION_KEYS
ERROR_MESSAGES: Final[dict[str, str]] = config.ERROR_MESSAGES
SUCCESS_MESSAGES: Final[dict[str, str]] = config.SUCCESS_MESSAGES
CSS_CLASSES: Final[dict[str, str]] = config.CSS_CLASSES
SUPPORTED_EXTENSIONS: Final[set[str]] = config.SUPPORTED_EXTENSIONS
EXPORT_EXTENSIONS: Final[dict[str, str]] = config.EXPORT_EXTENSIONS
MIME_TYPES: Final[dict[str, str]] = config.MIME_TYPES
COLUMN_MAPPINGS: Final[dict[str, dict[str, str]]] = config.COLUMN_MAPPINGS
AGGRID_CONFIG: Final[dict[str, Any]] = config.AGGRID_CONFIG 