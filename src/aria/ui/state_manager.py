"""Session state management for ARIA application.

This module provides centralized session state management with type safety
and helper methods for common state operations.
"""

import streamlit as st
import os
import tempfile
import uuid
import atexit
import shutil
import pandas as pd
from typing import Any, Optional, Dict, List
from pathlib import Path

from aria.core.types import ProcessingStep, UploadedFile, Question, Answer
from aria.core.logging_config import get_logger
from aria.config.config import SESSION_KEYS, DEFAULT_QUESTION_EXTRACTION_MODEL, DEFAULT_CUSTOM_PROMPT

logger = get_logger(__name__)


class StateManager:
    """Manages Streamlit session state for the ARIA application."""
    
    def __init__(self) -> None:
        """Initialize the state manager and ensure required keys exist."""
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state with default values."""
        # Create temporary directory for file storage if not exists
        if SESSION_KEYS["TEMP_DIR"] not in st.session_state:
            temp_dir = os.path.join(tempfile.gettempdir(), 'streamlit_app', str(uuid.uuid4()))
            os.makedirs(temp_dir, exist_ok=True)
            st.session_state[SESSION_KEYS["TEMP_DIR"]] = temp_dir
            
            # Clean up temporary files when the app is closed
            atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        # Initialize step management
        if SESSION_KEYS["STEP"] not in st.session_state:
            st.session_state[SESSION_KEYS["STEP"]] = ProcessingStep.UPLOAD
        
        # Initialize document information
        if SESSION_KEYS["RFI_NAME"] not in st.session_state:
            st.session_state[SESSION_KEYS["RFI_NAME"]] = ""
        
        # Initialize file upload state
        if SESSION_KEYS["UPLOADED_FILE"] not in st.session_state:
            st.session_state[SESSION_KEYS["UPLOADED_FILE"]] = None
        if SESSION_KEYS["UPLOADED_FILE_PATH"] not in st.session_state:
            st.session_state[SESSION_KEYS["UPLOADED_FILE_PATH"]] = None
        if SESSION_KEYS["TEMP_UPLOADED_FILE_PATH"] not in st.session_state:
            st.session_state[SESSION_KEYS["TEMP_UPLOADED_FILE_PATH"]] = None
        
        # Initialize question extraction state
        if SESSION_KEYS["QUESTIONS"] not in st.session_state:
            st.session_state[SESSION_KEYS["QUESTIONS"]] = []
        if SESSION_KEYS["OTHER_DATA"] not in st.session_state:
            st.session_state[SESSION_KEYS["OTHER_DATA"]] = {}
        if SESSION_KEYS["DF_INPUT"] not in st.session_state:
            st.session_state[SESSION_KEYS["DF_INPUT"]] = None
        if SESSION_KEYS["EXTRACTION_COMPLETE"] not in st.session_state:
            st.session_state[SESSION_KEYS["EXTRACTION_COMPLETE"]] = False
        if SESSION_KEYS["custom_extraction_prompt"] not in st.session_state:
            st.session_state[SESSION_KEYS["custom_extraction_prompt"]] = ""
        
        # Initialize answer generation state
        if SESSION_KEYS["GENERATED_ANSWERS"] not in st.session_state:
            st.session_state[SESSION_KEYS["GENERATED_ANSWERS"]] = []
        if SESSION_KEYS["GENERATED_ANSWERS_DF"] not in st.session_state:
            st.session_state[SESSION_KEYS["GENERATED_ANSWERS_DF"]] = pd.DataFrame()
        if SESSION_KEYS["GENERATION_COMPLETE"] not in st.session_state:
            st.session_state[SESSION_KEYS["GENERATION_COMPLETE"]] = False
        if SESSION_KEYS["SELECTED_QUESTIONS"] not in st.session_state:
            st.session_state[SESSION_KEYS["SELECTED_QUESTIONS"]] = []
        if SESSION_KEYS["custom_prompt"] not in st.session_state:
            st.session_state[SESSION_KEYS["custom_prompt"]] = DEFAULT_CUSTOM_PROMPT
        
        # Initialize export state
        if SESSION_KEYS["EXPORT_ANSWERS_DF"] not in st.session_state:
            st.session_state[SESSION_KEYS["EXPORT_ANSWERS_DF"]] = pd.DataFrame()
        if SESSION_KEYS["OUTPUT_PATH"] not in st.session_state:
            st.session_state[SESSION_KEYS["OUTPUT_PATH"]] = None
        if SESSION_KEYS["OUTPUT_FILE_NAME"] not in st.session_state:
            st.session_state[SESSION_KEYS["OUTPUT_FILE_NAME"]] = ""
        
        # Initialize file preview state
        if SESSION_KEYS["CURRENT_PREVIEW_FILE"] not in st.session_state:
            st.session_state[SESSION_KEYS["CURRENT_PREVIEW_FILE"]] = None
        
        # Initialize execution time tracking
        if SESSION_KEYS["EXECUTION_TIME"] not in st.session_state:
            st.session_state[SESSION_KEYS["EXECUTION_TIME"]] = 0.0
    
    def get_current_step(self) -> int:
        """Get the current processing step."""
        return st.session_state.get(SESSION_KEYS["STEP"], ProcessingStep.UPLOAD)
    
    def set_current_step(self, step: int) -> None:
        """Set the current processing step."""
        st.session_state[SESSION_KEYS["STEP"]] = step
        logger.info(f"Step changed to: {step}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from session state."""
        return st.session_state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in session state."""
        st.session_state[key] = value
    
    def clear(self) -> None:
        """Clear all session state."""
        temp_dir = st.session_state.get(SESSION_KEYS["TEMP_DIR"])
        
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Could not clean up temp directory: {e}")
        
        self._initialize_session_state()
        logger.info("Session state cleared and reinitialized")
    
    def reset_to_step(self, step: int) -> None:
        """Reset session state and go to a specific step."""
        # Keep essential information but clear step-specific data
        rfi_name = self.get(SESSION_KEYS["RFI_NAME"], "")
        uploaded_file = self.get(SESSION_KEYS["UPLOADED_FILE"])
        uploaded_file_path = self.get(SESSION_KEYS["UPLOADED_FILE_PATH"])
        
        if step <= ProcessingStep.UPLOAD:
            # Reset everything
            self.clear()
        elif step <= ProcessingStep.EXTRACT:
            # Keep upload data, clear extraction and later steps
            self.set(SESSION_KEYS["QUESTIONS"], [])
            self.set(SESSION_KEYS["DF_INPUT"], None)
            self.set(SESSION_KEYS["EXTRACTION_COMPLETE"], False)
            self._clear_generation_data()
            self._clear_export_data()
        elif step <= ProcessingStep.GENERATE:
            # Keep upload and extraction data, clear generation and later steps
            self._clear_generation_data()
            self._clear_export_data()
        elif step <= ProcessingStep.DOWNLOAD:
            # Keep all data except export
            self._clear_export_data()
        
        self.set_current_step(step)
    
    def _clear_generation_data(self) -> None:
        """Clear answer generation related data."""
        self.set(SESSION_KEYS["GENERATED_ANSWERS"], [])
        self.set(SESSION_KEYS["GENERATED_ANSWERS_DF"], pd.DataFrame())
        self.set(SESSION_KEYS["GENERATION_COMPLETE"], False)
        self.set(SESSION_KEYS["SELECTED_QUESTIONS"], [])
    
    def _clear_export_data(self) -> None:
        """Clear export related data."""
        self.set(SESSION_KEYS["EXPORT_ANSWERS_DF"], pd.DataFrame())
        self.set(SESSION_KEYS["OUTPUT_PATH"], None)
        self.set(SESSION_KEYS["OUTPUT_FILE_NAME"], "")
    
    # Document and file management methods
    def get_temp_dir(self) -> str:
        """Get the temporary directory path."""
        return self.get(SESSION_KEYS["TEMP_DIR"], tempfile.gettempdir())
    
    def set_document_info(self, name: str, uploaded_file: Any) -> None:
        """Set document information."""
        self.set(SESSION_KEYS["RFI_NAME"], name)
        self.set(SESSION_KEYS["UPLOADED_FILE"], uploaded_file)
        logger.info(f"Document info set: {name}")
    
    def get_document_name(self) -> str:
        """Get the document name."""
        return self.get(SESSION_KEYS["RFI_NAME"], "")
    
    def get_uploaded_file(self) -> Optional[Any]:
        """Get the uploaded file object."""
        return self.get(SESSION_KEYS["UPLOADED_FILE"])
    
    def set_file_paths(self, file_path: str, temp_path: Optional[str] = None) -> None:
        """Set file paths for uploaded file."""
        self.set(SESSION_KEYS["UPLOADED_FILE_PATH"], file_path)
        if temp_path:
            self.set(SESSION_KEYS["TEMP_UPLOADED_FILE_PATH"], temp_path)
        logger.info(f"File paths set: {file_path}")
    
    def get_file_path(self) -> Optional[str]:
        """Get the main uploaded file path."""
        return self.get(SESSION_KEYS["UPLOADED_FILE_PATH"])
    
    def get_temp_file_path(self) -> Optional[str]:
        """Get the temporary file path for preview."""
        return self.get(SESSION_KEYS["TEMP_UPLOADED_FILE_PATH"])
    
    # Question management methods
    def set_questions(self, questions: List[Dict], other_data: Optional[Dict] = None) -> None:
        """Set extracted questions."""
        self.set(SESSION_KEYS["QUESTIONS"], questions)
        self.set(SESSION_KEYS["OTHER_DATA"], other_data or {})
        self.set(SESSION_KEYS["EXTRACTION_COMPLETE"], True)
        
        # Convert to DataFrame if it's a list of dicts
        if questions and isinstance(questions[0], dict):
            df = pd.DataFrame(questions)
            self.set(SESSION_KEYS["DF_INPUT"], df)
        
        logger.info(f"Questions set: {len(questions)} questions")
    
    def get_questions(self) -> List[Dict]:
        """Get the extracted questions."""
        return self.get(SESSION_KEYS["QUESTIONS"], [])
    
    def get_questions_df(self) -> Optional[pd.DataFrame]:
        """Get the questions as DataFrame."""
        return self.get(SESSION_KEYS["DF_INPUT"])
    
    def update_questions_df(self, df: pd.DataFrame) -> None:
        """Update the questions DataFrame (for edits)."""
        self.set(SESSION_KEYS["DF_INPUT"], df)
        self.set(SESSION_KEYS["QUESTIONS"], df.to_dict('records'))
        logger.info("Questions DataFrame updated")
    
    def is_extraction_complete(self) -> bool:
        """Check if question extraction is complete."""
        return self.get(SESSION_KEYS["EXTRACTION_COMPLETE"], False)
    
    # Answer generation methods
    def set_generated_answers(self, answers: List, answers_df: Optional[pd.DataFrame] = None) -> None:
        """Set generated answers."""
        self.set(SESSION_KEYS["GENERATED_ANSWERS"], answers)
        if answers_df is not None:
            self.set(SESSION_KEYS["GENERATED_ANSWERS_DF"], answers_df)
        self.set(SESSION_KEYS["GENERATION_COMPLETE"], True)
        logger.info(f"Generated answers set: {len(answers)} answers")
    
    def get_generated_answers(self) -> List:
        """Get the generated answers."""
        return self.get(SESSION_KEYS["GENERATED_ANSWERS"], [])
    
    def get_generated_answers_df(self) -> pd.DataFrame:
        """Get the generated answers as DataFrame."""
        return self.get(SESSION_KEYS["GENERATED_ANSWERS_DF"], pd.DataFrame())
    
    def is_generation_complete(self) -> bool:
        """Check if answer generation is complete."""
        return self.get(SESSION_KEYS["GENERATION_COMPLETE"], False)
    
    def set_selected_questions(self, indices: List[int]) -> None:
        """Set selected question indices."""
        self.set(SESSION_KEYS["SELECTED_QUESTIONS"], indices)
    
    def get_selected_questions(self) -> List[int]:
        """Get selected question indices."""
        return self.get(SESSION_KEYS["SELECTED_QUESTIONS"], [])
    
    # Custom prompt methods
    def set_custom_prompt(self, prompt: str) -> None:
        """Set custom prompt for answer generation."""
        self.set(SESSION_KEYS["custom_prompt"], prompt)
    
    def get_custom_prompt(self) -> str:
        """Get custom prompt for answer generation."""
        return self.get(SESSION_KEYS["custom_prompt"], "")
    
    def set_custom_extraction_prompt(self, prompt: str) -> None:
        """Set custom prompt for question extraction."""
        self.set(SESSION_KEYS["custom_extraction_prompt"], prompt)
    
    def get_custom_extraction_prompt(self) -> str:
        """Get custom prompt for question extraction."""
        return self.get(SESSION_KEYS["custom_extraction_prompt"], "")
    
    def set_selected_extraction_model(self, model: str) -> None:
        """Set the selected model for question extraction."""
        self.set(SESSION_KEYS["SELECTED_EXTRACTION_MODEL"], model)
        logger.info(f"Selected extraction model set: {model}")
    
    def get_selected_extraction_model(self) -> str:
        """Get the selected model for question extraction."""
        return self.get(SESSION_KEYS["SELECTED_EXTRACTION_MODEL"], DEFAULT_QUESTION_EXTRACTION_MODEL)
    
    # Export methods
    def set_export_data(self, export_df: pd.DataFrame, file_name: str = "") -> None:
        """Set export data."""
        self.set(SESSION_KEYS["EXPORT_ANSWERS_DF"], export_df)
        if file_name:
            self.set(SESSION_KEYS["OUTPUT_FILE_NAME"], file_name)
        logger.info(f"Export data set: {len(export_df)} rows")
    
    def get_export_data(self) -> pd.DataFrame:
        """Get export data."""
        return self.get(SESSION_KEYS["EXPORT_ANSWERS_DF"], pd.DataFrame())
    
    def set_execution_time(self, time_minutes: float) -> None:
        """Set total execution time."""
        self.set(SESSION_KEYS["EXECUTION_TIME"], time_minutes)
    
    def get_execution_time(self) -> float:
        """Get total execution time."""
        return self.get(SESSION_KEYS["EXECUTION_TIME"], 0.0)
    
    # File preview management
    def update_file_preview(self, file_name: str) -> bool:
        """Update file preview status. Returns True if preview should be updated."""
        current_preview = self.get(SESSION_KEYS["CURRENT_PREVIEW_FILE"])
        if current_preview != file_name:
            self.set(SESSION_KEYS["CURRENT_PREVIEW_FILE"], file_name)
            return True
        return False
    
    def get_current_preview_file(self) -> Optional[str]:
        """Get the current preview file name."""
        return self.get(SESSION_KEYS["CURRENT_PREVIEW_FILE"])
    
    # Utility methods
    def has_uploaded_file(self) -> bool:
        """Check if a file has been uploaded."""
        return self.get_uploaded_file() is not None
    
    def has_questions(self) -> bool:
        """Check if questions have been extracted."""
        questions = self.get_questions()
        return len(questions) > 0
    
    def has_answers(self) -> bool:
        """Check if answers have been generated."""
        answers = self.get_generated_answers()
        return len(answers) > 0
    
    def get_step_status(self) -> Dict[str, bool]:
        """Get completion status for each step."""
        return {
            "upload": self.has_uploaded_file(),
            "extract": self.has_questions(),
            "generate": self.has_answers(),
            "download": not self.get_export_data().empty
        }
    

    
    def get_rfi_name(self) -> str:
        """Get the RFI/document name."""
        return self.get(SESSION_KEYS["RFI_NAME"], "")
    
    def set_df_input(self, df: pd.DataFrame) -> None:
        """Set the input DataFrame for questions."""
        self.set(SESSION_KEYS["DF_INPUT"], df)
        logger.info(f"Input DataFrame set with {len(df)} rows")
    
    def get_df_input(self) -> Optional[pd.DataFrame]:
        """Get the input DataFrame for questions."""
        return self.get(SESSION_KEYS["DF_INPUT"])
    
    def clear_questions(self) -> None:
        """Clear extracted questions data."""
        self.set(SESSION_KEYS["QUESTIONS"], [])
        self.set(SESSION_KEYS["DF_INPUT"], None)
        self.set(SESSION_KEYS["EXTRACTION_COMPLETE"], False)
        logger.info("Questions data cleared")
    
    def clear_answers(self) -> None:
        """Clear generated answers data."""
        self.set(SESSION_KEYS["GENERATED_ANSWERS"], [])
        self.set(SESSION_KEYS["GENERATED_ANSWERS_DF"], pd.DataFrame())
        self.set(SESSION_KEYS["GENERATION_COMPLETE"], False)
        logger.info("Answers data cleared")
    
    def set_generated_answers_df(self, df: pd.DataFrame) -> None:
        """Set the generated answers DataFrame."""
        self.set(SESSION_KEYS["GENERATED_ANSWERS_DF"], df)
        logger.info(f"Generated answers DataFrame set with {len(df)} rows")
    
    def set_export_answers_df(self, df: pd.DataFrame) -> None:
        """Set the export answers DataFrame."""
        self.set(SESSION_KEYS["EXPORT_ANSWERS_DF"], df)
        logger.info(f"Export answers DataFrame set with {len(df)} rows")
    
    def set_output_file_name(self, filename: str) -> None:
        """Set the output filename for export."""
        self.set(SESSION_KEYS["OUTPUT_FILE_NAME"], filename)
        logger.info(f"Output filename set: {filename}")
    
    def reset_session(self) -> None:
        """Reset the entire session (alias for clear)."""
        self.clear()
        logger.info("Session reset completed") 