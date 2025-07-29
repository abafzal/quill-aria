"""File preview component for Quill application.

This module provides a file preview component for displaying uploaded files
and their metadata in the sidebar.
"""

import streamlit as st
import pandas as pd
import os
from typing import Optional, Dict, Any
from pathlib import Path

from aria.ui.state_manager import StateManager
from aria.core.logging_config import log_info, log_warning, log_error


def render_file_preview(state_manager: StateManager) -> None:
    """Render file preview in the sidebar.
    
    Args:
        state_manager: State manager instance
    """
    st.sidebar.title("Document Preview")
    
    # Add ad hoc questions button at the top
    _render_adhoc_questions_button()
    
    # Show chat history if in ad hoc mode
    if st.session_state.get('show_adhoc_questions', False):
        _render_chat_history_sidebar()
    else:
        # Show regular file preview
        # Get file paths from state manager
        display_file_path = _get_display_file_path(state_manager)
        
        if display_file_path and os.path.exists(display_file_path):
            _render_file_info(display_file_path)
            _render_file_content(display_file_path)
        else:
            _render_no_file_message()
        
        # Add connection status indicator
        _render_connection_status()


def _render_adhoc_questions_button() -> None:
    """Render ad hoc questions access button."""
    st.sidebar.markdown("---")
    
    # Check if we're in ad hoc mode
    in_adhoc_mode = st.session_state.get('show_adhoc_questions', False)


def _get_display_file_path(state_manager: StateManager) -> Optional[str]:
    """Get the file path to display in preview.
    
    Args:
        state_manager: State manager instance
        
    Returns:
        File path to display, or None if no file available
    """
    # First check for temporary file path (during upload)
    temp_path = state_manager.get_temp_file_path()
    if temp_path and os.path.exists(temp_path):
        return temp_path
    
    # Then check for main file path (after processing)
    main_path = state_manager.get_file_path()
    if main_path and os.path.exists(main_path):
        return main_path
    
    return None


def _render_file_info(file_path: str) -> None:
    """Render file information section.
    
    Args:
        file_path: Path to the file
    """
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    st.sidebar.markdown(f"""
        <div style="padding: 0.5rem; border-radius: 4px; background-color: #e3f2fd; margin-bottom: 1rem;">
            <div style="font-size: 0.85rem; margin-top: 0.3rem; color: #212121;">{file_name}</div>
            <div style="font-size: 0.75rem; color: #5c6bc0; margin-top: 0.2rem;">{file_size/1024:.1f} KB</div>
        </div>
    """, unsafe_allow_html=True)


def _render_file_content(file_path: str) -> None:
    """Render file content preview based on file type.
    
    Args:
        file_path: Path to the file
    """
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1].lower()
    
    try:
        if file_extension in ['.html', '.htm']:
            _render_html_preview(file_path)
        elif file_extension == '.csv':
            _render_csv_preview(file_path)
        else:
            st.sidebar.warning(f"Preview not available for {file_extension} files")
    
    except Exception as e:
        log_error(f"Error rendering file preview: {str(e)}")
        st.sidebar.error(f"Could not preview file: {str(e)}")


def _render_html_preview(file_path: str) -> None:
    """Render HTML file preview.
    
    Args:
        file_path: Path to the HTML file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Show a preview using iframe
        height = 600
        html_preview = f"""
        <div style="border: 1px solid #e0e0e0; border-radius: 4px; padding: 0;">
            <iframe srcdoc="{html_content.replace('"', '&quot;')}" 
                    width="100%" 
                    height="{height}px" 
                    style="border: none;">
            </iframe>
        </div>
        """
        st.sidebar.markdown(html_preview, unsafe_allow_html=True)
        
        log_info(f"HTML preview rendered: {len(html_content)} bytes")
    
    except Exception as e:
        log_warning(f"Could not display HTML: {str(e)}")
        st.sidebar.warning(f"Could not display HTML: {str(e)}")


def _render_csv_preview(file_path: str) -> None:
    """Render CSV file preview.
    
    Args:
        file_path: Path to the CSV file
    """
    try:
        df = pd.read_csv(file_path)
        st.sidebar.markdown("### CSV Preview")
        st.sidebar.dataframe(df.head(5), use_container_width=True, height=200)
        
        # Show basic info
        st.sidebar.markdown(f"""
        <div style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">
            📊 {len(df)} rows × {len(df.columns)} columns
        </div>
        """, unsafe_allow_html=True)
        
        log_info(f"CSV preview rendered: {len(df)} rows, {len(df.columns)} columns")
    
    except Exception as e:
        log_warning(f"Could not preview CSV: {str(e)}")
        st.sidebar.warning(f"Could not preview CSV: {str(e)}")


def _render_no_file_message() -> None:
    """Render message when no file is available."""
    st.sidebar.markdown("""
    <div style="padding: 1rem; border-radius: 4px; background-color: #f5f5f5; 
         text-align: center; margin: 1rem 0; border: 1px dashed #bdbdbd;">
        <div style="color: #333333; font-size: 0.9rem; font-weight: 500;">No document uploaded yet</div>
        <div style="color: #555555; font-size: 0.8rem; margin-top: 0.5rem;">
            Upload a document to see the preview here
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_connection_status() -> None:
    """Render connection status indicator at bottom of sidebar."""
    import os
    from aria.config.config import config
    
    # Check if we have valid Databricks configuration
    has_host = config.databricks.host and config.databricks.host != "http://localhost"
    
    # Check for authentication - either Service Principal or Token
    has_auth = bool(
        os.getenv('DATABRICKS_CLIENT_ID') or  # Service Principal
        os.getenv('DATABRICKS_TOKEN')        # Personal Access Token
    )
    
    is_connected = has_host and has_auth
    
    connection_status = "✅ Connected" if is_connected else "❌ Not connected"
    connection_color = "#4CAF50" if is_connected else "#F44336"
    
    st.sidebar.markdown(f"""
    <div style="position: fixed; bottom: 0; left: 0; width: 18rem; 
         background-color: #f8f9fa; border-top: 1px solid #eaecef; 
         padding: 0.5rem; font-size: 0.75rem; color: #333333;
         display: flex; align-items: center; justify-content: center;">
        <span style="color: {connection_color}; font-weight: 500;">{connection_status}</span>
        <span style="margin-left: 0.3rem; font-weight: 500;">to Databricks</span>
    </div>
    """, unsafe_allow_html=True)


def render_detailed_file_info(state_manager: StateManager) -> None:
    """Render detailed file information in the main content area.
    
    Args:
        state_manager: State manager instance
    """
    file_path = _get_display_file_path(state_manager)
    
    if not file_path or not os.path.exists(file_path):
        st.info("No file information available")
        return
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Create columns for file info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("File Name", file_name)
    
    with col2:
        st.metric("File Size", f"{file_size/1024:.1f} KB")
    
    with col3:
        st.metric("File Type", file_extension.upper())
    
    # Show basic file type info
    if file_extension == '.csv':
        st.info("📊 CSV file - will be processed to extract questions from question columns")
    elif file_extension in ['.html', '.htm']:
        st.info("🌐 HTML file - will be processed using AI to extract questions")


def _render_chat_history_sidebar() -> None:
    """Render chat history in sidebar (ChatGPT style)."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Chat History")
    
    # Get chat history
    chat_history = st.session_state.get('adhoc_chat_history', [])
    
    if not chat_history:
        st.sidebar.markdown("""
        <div style="padding: 1rem; border-radius: 4px; background-color: #f5f5f5; 
             text-align: center; margin: 1rem 0; border: 1px dashed #bdbdbd;">
            <div style="color: #666; font-size: 0.8rem;">No questions yet</div>
            <div style="color: #888; font-size: 0.7rem; margin-top: 0.3rem;">
                Start asking questions to see them here
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show recent questions (last 10)
    recent_questions = chat_history[-10:] if len(chat_history) > 10 else chat_history
    
    for i, message in enumerate(reversed(recent_questions)):
        question_text = message['question']
        # Truncate long questions for sidebar display
        display_text = question_text[:50] + "..." if len(question_text) > 50 else question_text
        
        # Create a clickable question item
        question_key = f"sidebar_q_{len(chat_history)-i-1}"
        
        # Show timestamp
        timestamp = message.get('timestamp', 'Unknown')
        time_display = timestamp.split(' ')[1][:5] if ' ' in timestamp else timestamp[:10]
        
        # Status icon
        status_icon = "❌" if message.get('error') else "✅"
        
        # Create button for each question
        button_text = f"{status_icon} {display_text}"
        if st.sidebar.button(button_text, key=question_key, help=f"Asked at {timestamp}\n\nClick to view in main chat"):
            # Scroll to this question in main chat (via session state)
            st.session_state['selected_question_index'] = len(chat_history) - i - 1
    
    # Show total count
    if len(chat_history) > 10:
        st.sidebar.caption(f"Showing last 10 of {len(chat_history)} questions")


 