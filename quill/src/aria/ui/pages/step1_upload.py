"""Step 1: File Upload page for ARIA application.

This module handles the file upload and document name input functionality.
"""

import streamlit as st
import os
import time
from typing import Optional
import shutil
from pathlib import Path

from aria.ui.state_manager import StateManager
from aria.config.config import (
    config, SUPPORTED_FILE_TYPES, ERROR_MESSAGES, SUCCESS_MESSAGES,
    MAX_FILE_SIZE_MB
)
from aria.core.logging_config import log_info, log_error, log_success
from aria.core.exceptions import FileProcessingError, UnsupportedFileTypeError


def render_upload_page(state_manager: StateManager) -> None:
    """Render the file upload page.
    
    Args:
        state_manager: State manager instance
    """
    st.info("Upload your document in CSV or HTML format.")
    
    # RFI information form
    current_name = state_manager.get_document_name()
    rfi_name = st.text_input("Document name:", value=current_name)
    
    # File upload section
    uploaded_file = st.file_uploader(
        "Choose and upload a CSV or HTML file here", 
        type=["csv", "html", "htm"],
        help=f"Maximum file size: {MAX_FILE_SIZE_MB}MB. Supported formats: {', '.join(SUPPORTED_FILE_TYPES)}"
    )
    st.caption("Tip: Don’t have a file handy? Use our sample CSV or download it to learn the expected format.")
    
    # Layout: two columns for actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Use sample CSV", key="use_sample_csv"):
            _use_sample_csv(state_manager)
            return
    with col2:
        _render_download_sample_button()
    
    # Handle file upload for preview
    if uploaded_file:
        _handle_file_preview(state_manager, uploaded_file)
    
    # Process button
    if st.button("Next step", key="next_step1", type="primary"):
        if _validate_inputs(rfi_name, uploaded_file):
            _process_upload(state_manager, rfi_name, uploaded_file)


def _handle_file_preview(state_manager: StateManager, uploaded_file) -> None:
    """Handle file upload for sidebar preview.
    
    Args:
        state_manager: State manager instance
        uploaded_file: Streamlit uploaded file object
    """
    try:
        # Save the file temporarily for preview
        temp_dir = state_manager.get_temp_dir()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_file_path, 'wb') as output_file:
            output_file.write(uploaded_file.read())
        
        # Reset file pointer for later use
        uploaded_file.seek(0)
        
        # Update preview only if file changed
        if state_manager.update_file_preview(uploaded_file.name):
            state_manager.set_file_paths(temp_file_path, temp_file_path)
            log_info(f"File preview updated: {uploaded_file.name}")
            st.rerun()
    
    except Exception as e:
        log_error(f"Error handling file preview: {str(e)}")
        st.error(f"Error processing file for preview: {str(e)}")


def _use_sample_csv(state_manager: StateManager) -> None:
    """Load the bundled sample CSV into the session and advance to next step."""
    try:
        # Resolve path to src/assets/sample-questions.csv relative to this file
        current_file_dir = Path(__file__).resolve().parent
        sample_src_path = (current_file_dir / ".." / ".." / ".." / "assets" / "sample-questions.csv").resolve()
        if not sample_src_path.exists():
            raise FileNotFoundError(f"Sample file not found at {sample_src_path}")
        
        # Copy to temp directory to behave like an uploaded file
        temp_dir = Path(state_manager.get_temp_dir())
        temp_dir.mkdir(parents=True, exist_ok=True)
        sample_dest_path = temp_dir / "sample-questions.csv"
        shutil.copyfile(sample_src_path, sample_dest_path)
        
        # Update state: set document info, file paths, show preview
        state_manager.set_document_info("Sample Questions", uploaded_file=None)
        state_manager.set_file_paths(str(sample_dest_path), str(sample_dest_path))
        _show_csv_preview(str(sample_dest_path), state_manager)
        log_success("Sample CSV loaded successfully")
        
        # Advance to next step
        state_manager.set_current_step(2)
        st.rerun()
    except Exception as e:
        log_error(f"Error loading sample CSV: {str(e)}")
        st.error(f"Could not load sample CSV: {str(e)}")


def _render_download_sample_button() -> None:
    """Render a button to download the sample CSV."""
    try:
        current_file_dir = Path(__file__).resolve().parent
        sample_src_path = (current_file_dir / ".." / ".." / ".." / "assets" / "sample-questions.csv").resolve()
        if not sample_src_path.exists():
            st.button("Download sample CSV", disabled=True, help="Sample file not found")
            return
        with open(sample_src_path, "rb") as f:
            st.download_button(
                label="Download sample CSV",
                data=f.read(),
                file_name="sample-questions.csv",
                mime="text/csv",
                key="download_sample_csv"
            )
    except Exception as e:
        st.button("Download sample CSV", disabled=True, help=str(e))

 
def _validate_inputs(rfi_name: str, uploaded_file) -> bool:
    """Validate user inputs.
    
    Args:
        rfi_name: Document name entered by user
        uploaded_file: Uploaded file object
        
    Returns:
        True if inputs are valid, False otherwise
    """
    valid = True
    
    if not rfi_name or not rfi_name.strip():
        st.error("Please enter a document name.")
        valid = False
    
    if not uploaded_file:
        st.error("Please upload a CSV or HTML file.")
        valid = False
    else:
        # Validate file type
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in SUPPORTED_FILE_TYPES:
            st.error(ERROR_MESSAGES["UNSUPPORTED_FILE_TYPE"].format(file_type=file_extension))
            valid = False
        
        # Validate file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB).")
            valid = False
    
    return valid


def _process_upload(state_manager: StateManager, rfi_name: str, uploaded_file) -> None:
    """Process the file upload and advance to next step.
    
    Args:
        state_manager: State manager instance
        rfi_name: Document name
        uploaded_file: Uploaded file object
    """
    try:
        with st.spinner("Processing uploaded file..."):
            # Save file to permanent location
            temp_dir = state_manager.get_temp_dir()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(file_path, 'wb') as output_file:
                output_file.write(uploaded_file.read())
            
            # Store information in state
            state_manager.set_document_info(rfi_name.strip(), uploaded_file)
            state_manager.set_file_paths(file_path, file_path)
            
            # Show preview for CSV files
            _show_csv_preview(file_path, state_manager)
            
            log_success(f"File upload completed: {uploaded_file.name}")
            
            # Advance to next step
            state_manager.set_current_step(2)
            st.rerun()
    
    except Exception as e:
        log_error(f"Error processing upload: {str(e)}")
        st.error(f"Error processing file: {str(e)}")


def _show_csv_preview(file_path: str, state_manager: StateManager) -> None:
    """Show preview for CSV files.
    
    Args:
        file_path: Path to the uploaded file
        state_manager: State manager instance
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.csv':
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Store in state for potential use in next step
            state_manager.set("df_input", df)
            
            # Show preview
            st.subheader("File Preview")
            st.dataframe(df.head(), use_container_width=True)
            
            log_info(f"CSV preview shown: {len(df)} rows, {len(df.columns)} columns")
        
        except Exception as e:
            log_error(f"Error previewing CSV: {str(e)}")
            st.error(f"Error previewing CSV file: {str(e)}")