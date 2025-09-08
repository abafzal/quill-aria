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


def initialize_application() -> None:
    """Initialize the application with logging and configuration."""
    # Set up logging
    logger = setup_logging(level="INFO")
    
    # Log application startup
    log_info("ARIA application starting up")
    
    # Log configuration (without sensitive data)
    config.log_configuration()
    
    # Validate configuration
    is_valid, errors = config.validate_configuration()
    if not is_valid:
        log_error("Configuration validation failed")
        st.error("Configuration errors detected:")
        for error in errors:
            st.error(f"• {error}")
        st.stop()
    
    log_info("Application initialization completed successfully")


def render_header() -> None:
    """Render the application header."""
    # Load fonts and header CSS
    load_font_imports()
    load_header_css()
    
    # Custom header HTML with domain-specific title
    st.markdown(f"""
    <div id="customHeader">
        <h1>{config.domain.app_title}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Add spacer so content doesn't hide behind header
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)


def render_sidebar(state_manager: StateManager) -> None:
    """Render the sidebar with mode switcher and context-specific content.
    
    Args:
        state_manager: State manager instance
    """
    # Detect if any critical operation is in progress
    extraction_in_progress = st.session_state.get(SESSION_KEYS["EXTRACTION_IN_PROGRESS"], False)
    generation_in_progress = st.session_state.get(SESSION_KEYS["GENERATION_IN_PROGRESS"], False)
    adhoc_processing = st.session_state.get('adhoc_processing', False)
    mode_switch_disabled = extraction_in_progress or generation_in_progress or adhoc_processing

    # Mode switcher at the top (dropdown, widget state is source of truth)
    mode_options = ["Document Processing", "Chat"]
    selected_mode = st.sidebar.selectbox(
        "Choose Mode",
        options=mode_options,
        key="mode_switcher",
        help="Switching modes is disabled while a process is running.",
        disabled=mode_switch_disabled
    )
    st.session_state["mode"] = "document" if selected_mode == "Document Processing" else "chat"

    if mode_switch_disabled:
        st.sidebar.info("🔒 Mode switching is disabled while processing. Please wait for the current operation to finish.")

    # Load sidebar CSS
    load_sidebar_css()

    # Show sidebar content based on mode
    if st.session_state["mode"] == "document":
        render_file_preview(state_manager)
    elif st.session_state["mode"] == "chat":
        from aria.ui.pages.adhoc_questions import render_chat_sidebar
        render_chat_sidebar()


def main() -> None:
    """Main application function."""
    # Initialize application
    initialize_application()
    # Load main CSS styles
    load_custom_css()
    # Render header
    render_header()
    # Initialize state manager
    state_manager = StateManager()
    # Render sidebar (now includes mode switcher)
    render_sidebar(state_manager)

    # Display welcome message from domain config
    if state_manager.get_current_step() == ProcessingStep.UPLOAD and not st.session_state.get(SESSION_KEYS["uploaded_file"]):
        st.info("Upload your document to get started with AI-powered question extraction and answer generation.")

    # Route based on mode
    mode = st.session_state.get("mode", "document")
    if mode == "chat":
        render_adhoc_questions_page(state_manager)
        return
    # Document processing workflow
    current_step = state_manager.get_current_step()
    apply_step_specific_css(current_step)
    render_stepper(current_step)
    if current_step == ProcessingStep.UPLOAD:
        render_upload_page(state_manager)
    elif current_step == ProcessingStep.EXTRACT:
        render_extract_page(state_manager)
    elif current_step == ProcessingStep.GENERATE:
        render_generate_page(state_manager)
    elif current_step == ProcessingStep.DOWNLOAD:
        render_download_page(state_manager)
    else:
        log_error(f"Invalid step: {current_step}, resetting to upload")
        state_manager.set_current_step(ProcessingStep.UPLOAD)
        st.rerun()
    if config.app.debug:
        _render_debug_info(state_manager)


def _render_debug_info(state_manager: StateManager) -> None:
    """Render debug information for development.
    
    Args:
        state_manager: State manager instance
    """
    with st.expander("🔧 Debug Information", expanded=False):
        st.subheader("State Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Step Status:**")
            status = state_manager.get_step_status()
            for step, completed in status.items():
                icon = "✅" if completed else "❌"
                st.write(f"{icon} {step.title()}: {completed}")
        
        with col2:
            st.write("**Configuration:**")
            st.write(f"• Domain: {config.domain.domain_name}")
            st.write(f"• Host: {config.databricks.host}")
            auth_mode = "Service Principal" if os.getenv('DATABRICKS_CLIENT_ID') else "Token"
            st.write(f"• Auth: {auth_mode}")
            st.write(f"• Debug Mode: {config.app.debug}")
        
        st.write("**Session State Keys:**")
        session_keys = list(st.session_state.keys())
        st.write(f"Total keys: {len(session_keys)}")
        
        if st.checkbox("Show all session state"):
            for key in sorted(session_keys):
                value = st.session_state[key]
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 100:
                    display_value = f"{value[:100]}... (truncated)"
                elif hasattr(value, '__len__') and len(value) > 10:
                    display_value = f"{type(value).__name__} with {len(value)} items"
                else:
                    display_value = str(value)
                st.code(f"{key}: {display_value}")


if __name__ == "__main__":
    main() 