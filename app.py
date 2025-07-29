#!/usr/bin/env python3
"""Main application entry point for ARIA.

This is the new modular version of the ARIA application with improved
structure and separation of concerns.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path so we can import aria modules
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
from aria.ui.state_manager import StateManager
from aria.ui.components.stepper import render_stepper
from aria.ui.components.file_preview import render_file_preview
from aria.ui.styles.css import (
    load_custom_css, load_header_css, load_sidebar_css, 
    load_font_imports, apply_step_specific_css
)
from aria.ui.pages.step1_upload import render_upload_page
from aria.ui.pages.step2_extract import render_extract_page
from aria.ui.pages.step3_generate import render_generate_page
from aria.ui.pages.step4_download import render_download_page
from aria.ui.pages.adhoc_questions import render_adhoc_questions_page
from aria.config.config import config, SESSION_KEYS
from aria.core.logging_config import setup_logging, log_info, log_error
from aria.core.types import ProcessingStep

# Configure Streamlit page
st.set_page_config(
    page_title=config.domain.app_title,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
setup_logging()
log_info("Quill application starting up") 