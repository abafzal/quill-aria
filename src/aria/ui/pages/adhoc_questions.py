"""Ad hoc questions page for ARIA application.

This module provides a simple chat interface for asking individual questions
to the AI model without going through the full RFI workflow.
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from aria.ui.state_manager import StateManager
from aria.services.answer_generation import AnswerGenerationService
from aria.core.logging_config import get_logger
from aria.config.config import ERROR_MESSAGES, DEFAULT_TIMEOUT_SECONDS

logger = get_logger(__name__)

# Timer constants
TIMEOUT_SECONDS = DEFAULT_TIMEOUT_SECONDS  # 297 seconds ≈ 5 minutes


def render_adhoc_questions_page(state_manager: StateManager) -> None:
    """Render the ad hoc questions page.
    
    Args:
        state_manager: State manager instance
    """
    st.header("Chat")
    
    # Add data sources information
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #0066cc;">
        <div style="font-size: 14px; color: #495057; line-height: 1.4;">
            <strong>📚 Data Sources:</strong><br>
            <ul style="margin: 8px 0 0 20px; padding: 0;">
                <li>Regulatory and compliance requirements from governing agencies.</li>
                <li>Databricks system tables containing data access and lakeflow pipelines logs.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize ad hoc questions in session state if not exists
    _initialize_adhoc_state()
    
    # Check if we're currently processing a question
    if st.session_state.get('adhoc_processing', False):
        _handle_question_processing()
        return
    
    # Get chat history
    chat_history = st.session_state.get('adhoc_chat_history', [])
    selected_index = st.session_state.get('selected_question_index', None)
    
    # Display conversation history ABOVE the input form (like ChatGPT)
    if chat_history:
        _render_chat_history(chat_history, selected_index=selected_index)
    
    # Add separator
    st.markdown("---")
    
    # Question input form - always at the bottom
    _render_question_input()
    
    # Action buttons for managing history
    if chat_history:
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state['adhoc_chat_history'] = []
                st.session_state['selected_question_index'] = None
                st.rerun()
        
        with col2:
            if st.button("📋 Copy All", use_container_width=True):
                # Create text version of chat for copying
                chat_text = _format_chat_for_copy(chat_history)
                st.code(chat_text, language=None)
                st.success("💡 Chat history displayed above - use your browser to copy")
    
    logger.info("Ad hoc questions page rendered")


def _initialize_adhoc_state() -> None:
    """Initialize session state for ad hoc questions."""
    if 'adhoc_chat_history' not in st.session_state:
        st.session_state['adhoc_chat_history'] = []
    
    if 'adhoc_question_input' not in st.session_state:
        st.session_state['adhoc_question_input'] = ""
    
    if 'adhoc_processing' not in st.session_state:
        st.session_state['adhoc_processing'] = False
    
    if 'adhoc_current_question' not in st.session_state:
        st.session_state['adhoc_current_question'] = ""
    
    if 'adhoc_processing_start_time' not in st.session_state:
        st.session_state['adhoc_processing_start_time'] = None


def _handle_question_processing() -> None:
    """Handle the question processing state with real-time status display."""
    current_question = st.session_state.get('adhoc_current_question', '')
    # start_time = st.session_state.get('adhoc_processing_start_time', time.time()) # Keep for potential future use but not for status here
    
    # Get chat history
    chat_history = st.session_state.get('adhoc_chat_history', [])
    
    # Display conversation history INCLUDING the current processing question
    if chat_history:
        _render_chat_history(chat_history)
    
    # Show the current question being processed
    st.markdown("---")
    with st.chat_message("user"):
        st.write(f"**Q:** {current_question}")
        st.caption(f"Asked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Activate spinner here, then call the processing function
    with st.spinner("Thinking... This may take up to 5 minutes."):
        _process_question_async(current_question)


def _render_chat_history(chat_history: List[Dict[str, Any]], selected_index: Optional[int] = None) -> None:
    """Render the chat history display, highlighting the selected chat if any.
    
    Args:
        chat_history: List of chat messages
        selected_index: Index of the selected chat (optional)
    """
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(chat_history):
            timestamp = message.get('timestamp', 'Unknown time')
            highlight = (selected_index == i)
            user_style = "background-color: #fffde7; border-left: 4px solid #1976D2;" if highlight else ""
            ai_style = "background-color: #e3f2fd; border-left: 4px solid #1976D2;" if highlight else ""
            # User question
            with st.chat_message("user"):
                st.markdown(f'<div style="{user_style}"><strong>Q:</strong> {message["question"]}<br><span style="font-size: 0.85em; color: #888;">Asked at {timestamp}</span></div>', unsafe_allow_html=True)
            # AI answer
            with st.chat_message("assistant"):
                if message.get('error'):
                    st.markdown(f'<div style="{ai_style}"><span style="color: #d32f2f; font-weight: bold;">❌ Error:</span> {message["error"]}</div>', unsafe_allow_html=True)
                    if st.button(f"🔄 Retry", key=f"retry_{i}", help="Retry this question"):
                        st.session_state['adhoc_processing'] = True
                        st.session_state['adhoc_current_question'] = message['question']
                        st.session_state['adhoc_processing_start_time'] = time.time()
                        st.rerun()
                else:
                    st.markdown(f'<div style="{ai_style}"><strong>A:</strong> {message["answer"]}</div>', unsafe_allow_html=True)
                    if message.get('generation_time'):
                        st.caption(f"Generated in {message['generation_time']:.1f} seconds")
                    if st.button("📄", key=f"copy_a_{i}", help="Copy answer"):
                        st.code(message['answer'], language=None)
                        st.success("💡 Answer displayed above - use your browser to copy")


def _render_question_input() -> None:
    """Render the question input form."""
    with st.form(key="adhoc_question_form", clear_on_submit=True):
        # Question input with improved styling
        question = st.text_area(
            "Your Question:",
            placeholder="Ask me anything about Databricks, data engineering, machine learning, or any other topic. Feel free to set character limits if needed.",
            height=120,
            help="Ask any question - technical, product-related, or general inquiries. Press Ctrl+Enter to submit.",
            label_visibility="collapsed"
        )
        
        # Submit button with improved styling
        submitted = st.form_submit_button("🚀 Send", type="primary", use_container_width=True)
        
        if submitted and question.strip():
            # Set processing state immediately
            st.session_state['adhoc_processing'] = True
            st.session_state['adhoc_current_question'] = question.strip()
            st.session_state['adhoc_processing_start_time'] = time.time()
            st.rerun()
        elif submitted and not question.strip():
            st.error("Please enter a question before submitting.")


def _show_simple_processing_status(start_time: float) -> None:
    """Show simple processing status with spinner and animated dots."""
    with st.spinner("Thinking... This may take up to 5 minutes."):
        elapsed_time = time.time() - start_time
        dots_count = (int(elapsed_time * 2) % 3) + 1
        dots = "." * dots_count
        st.info(f"**Thinking{dots}** (Times out after 5 minutes)")


def _show_processing_status(start_time: float) -> None:
    """Show processing status with simple progress indicator.
    
    Args:
        start_time: When processing started
    """
    elapsed_time = time.time() - start_time
    
    # Simple animated dots
    dots_count = int(elapsed_time * 2) % 4
    dots = "." * dots_count
    
    # Show status with elapsed time
    elapsed_mins, elapsed_secs = divmod(int(elapsed_time), 60)
    
    st.info(f"**Thinking{dots}** ({elapsed_mins:02d}:{elapsed_secs:02d})")
    
    # Show timeout warning if taking long
    if elapsed_time > 120:  # 2 minutes
        st.warning("⚠️ **Taking longer than expected.** For faster responses, try breaking complex questions into smaller parts.")
    elif elapsed_time > 60:  # 1 minute
        st.info("💡 **Tip:** Large documents or complex questions may take up to 5 minutes to process.")


def _process_question_async(question: str) -> None:
    """Process the user's question asynchronously.
    
    This function is now called within a spinner context from _handle_question_processing.
    
    Args:
        question: The user's question
    """
    # Initialize the answer generation service
    generation_service = AnswerGenerationService()
    
    # Check authentication
    auth_headers = generation_service.settings.get_auth_headers()
    if not auth_headers:
        st.error("❌ **Authentication Error**: Unable to connect to AI model. Please check your Databricks configuration.")
        st.session_state['adhoc_processing'] = False
        # Consider adding st.rerun() here if the page should refresh immediately on auth error
        return
    
    try:
        processing_start_time = st.session_state.get('adhoc_processing_start_time', time.time())
        
        # Create a question dict in the format expected by the service
        question_dict = {
            'id': f"adhoc_{int(time.time())}",
            'text': question,
            'Question': question,  # Some parts of the service might expect this key
            'topic': 'Ad Hoc Question'
        }
        
        # Generate answer using the service
        success, answer_dict = generation_service._generate_single_answer(
            question=question_dict,
            custom_prompt="",  # No custom prompt for ad hoc questions
            auth_headers=auth_headers
        )
        
        generation_time = time.time() - processing_start_time
        
        # Create chat message
        chat_message = {
            'question': question,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'generation_time': generation_time
        }
        
        if success and answer_dict:
            answer_text = answer_dict.get('answer', 'No answer generated')
            chat_message['answer'] = answer_text
            logger.info(f"Ad hoc question answered successfully in {generation_time:.1f}s")
        else:
            chat_message['error'] = "Failed to generate answer. Please try again."
            logger.warning(f"Ad hoc question failed: {question[:50]}...")
        
        if 'adhoc_chat_history' not in st.session_state:
            st.session_state['adhoc_chat_history'] = []
        st.session_state['adhoc_chat_history'].append(chat_message)
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing ad hoc question: {error_message}")
        is_timeout = any(timeout_keyword in error_message.lower() 
                        for timeout_keyword in ['timeout', 'timed out', 'read timeout'])
        error_text = (
            f"Request timed out after {TIMEOUT_SECONDS//60} minutes. Try breaking your question into smaller parts."
            if is_timeout else f"Unexpected error: {error_message}"
        )
        error_chat_message = {
            'question': question,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'error': error_text
        }
        if 'adhoc_chat_history' not in st.session_state:
            st.session_state['adhoc_chat_history'] = []
        st.session_state['adhoc_chat_history'].append(error_chat_message)
    finally:
        # Clear processing state and rerun regardless of success or failure
        st.session_state['adhoc_processing'] = False
        st.session_state['adhoc_current_question'] = ""
        st.session_state['adhoc_processing_start_time'] = None
        st.rerun()


def _format_chat_for_copy(chat_history: List[Dict[str, Any]]) -> str:
    """Format chat history as copyable text.
    
    Args:
        chat_history: List of chat messages
        
    Returns:
        Formatted text string
    """
    lines = ["=== ARIA Ad Hoc Questions Chat History ===\n"]
    
    for i, message in enumerate(chat_history, 1):
        lines.append(f"Q{i}: {message['question']}")
        
        if message.get('error'):
            lines.append(f"A{i}: ERROR - {message['error']}")
        else:
            lines.append(f"A{i}: {message.get('answer', 'No answer')}")
        
        lines.append(f"Time: {message.get('timestamp', 'Unknown')}")
        lines.append("")  # Empty line between exchanges
    
    return "\n".join(lines)


def render_chat_sidebar() -> None:
    """Render chat history in the sidebar for Chat mode."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Chat History")
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
        display_text = question_text[:50] + "..." if len(question_text) > 50 else question_text
        question_key = f"sidebar_q_{len(chat_history)-i-1}"
        timestamp = message.get('timestamp', 'Unknown')
        time_display = timestamp.split(' ')[1][:5] if ' ' in timestamp else timestamp[:10]
        status_icon = "❌" if message.get('error') else "✅"
        button_text = f"{status_icon} {display_text}"
        if st.sidebar.button(button_text, key=question_key, help=f"Asked at {timestamp}\n\nClick to view in main chat"):
            st.session_state['selected_question_index'] = len(chat_history) - i - 1
    if len(chat_history) > 10:
        st.sidebar.caption(f"Showing last 10 of {len(chat_history)} questions")
    st.sidebar.markdown("---") 