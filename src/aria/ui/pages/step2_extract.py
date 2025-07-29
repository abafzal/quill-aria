"""Step 2: Question Extraction page for ARIA application.

This module handles the question extraction and review functionality.
"""

import streamlit as st
import pandas as pd
import time
from typing import Optional

from aria.ui.state_manager import StateManager
from aria.core.logging_config import get_logger
from aria.services import DocumentProcessor, QuestionExtractionService
from aria.config.config import ERROR_MESSAGES, SUCCESS_MESSAGES, AVAILABLE_CLAUDE_MODELS, DEFAULT_QUESTION_EXTRACTION_MODEL, DEFAULT_TIMEOUT_SECONDS, SESSION_KEYS

logger = get_logger(__name__)

# Timer constants
TIMEOUT_SECONDS = DEFAULT_TIMEOUT_SECONDS  # 297 seconds ≈ 5 minutes


def render_extract_page(state_manager: StateManager) -> None:
    """Render the question extraction page.
    
    Args:
        state_manager: State manager instance
    """
    # Add skip link for screen readers
    st.markdown("""
    <a href="#main-content" class="skip-link">Skip to main content</a>
    """, unsafe_allow_html=True)
    
    st.header("Step 2: Extract & Review Questions")
    
    # Add main content landmark
    st.markdown('<main id="main-content" role="main">', unsafe_allow_html=True)
    
    # Check if file has been uploaded
    if not state_manager.has_uploaded_file():
        st.error(ERROR_MESSAGES["NO_FILE_UPLOADED"])
        if st.button("← Back to Step 1", key="back_to_step1", help="Return to file upload step"):
            state_manager.set_current_step(1)
            st.rerun()
        st.markdown('</main>', unsafe_allow_html=True)
        return
    
    # Initialize services
    doc_processor = DocumentProcessor()
    extraction_service = QuestionExtractionService()
    
    # Show file information with custom styling and accessibility
    file_path = state_manager.get_file_path()
    if file_path:
        import os
        file_name = os.path.basename(file_path)
        st.markdown(f"""
        <div class="file-processing-info" role="status" aria-live="polite">
            📄 <strong>Processing file:</strong> {file_name}
        </div>
        """, unsafe_allow_html=True)
    
    # File validation section
    if file_path:
        # Validate the file
        is_valid, errors = doc_processor.validate_file(file_path)
        
        if not is_valid:
            st.error("File validation failed:")
            for error in errors:
                st.error(f"• {error}")
            st.markdown('</main>', unsafe_allow_html=True)
            return
    
    # Check if extraction is in progress
    extraction_in_progress = st.session_state.get(SESSION_KEYS["EXTRACTION_IN_PROGRESS"], False)
    
    # If extraction is in progress and we haven't started processing yet, start it
    if extraction_in_progress and not state_manager.has_questions():
        _extract_questions(state_manager, doc_processor, extraction_service, state_manager.get_custom_extraction_prompt())
        st.markdown('</main>', unsafe_allow_html=True)
        return
    
    # Question extraction section
    if not state_manager.has_questions():
        
        # Get current selection
        current_model = state_manager.get_selected_extraction_model()
        
        # Create model selection
        model_options = list(AVAILABLE_CLAUDE_MODELS.keys())
        model_labels = [AVAILABLE_CLAUDE_MODELS[model] for model in model_options]
        
        # Find current index
        try:
            # Try to find the model as a key first
            current_index = model_options.index(current_model)
        except ValueError:
            # If not found as key, check if it's a value in the available models
            model_values = list(AVAILABLE_CLAUDE_MODELS.values())
            if current_model in model_values:
                # Find the key for this value
                for i, (key, value) in enumerate(AVAILABLE_CLAUDE_MODELS.items()):
                    if value == current_model:
                        current_index = i
                        break
                else:
                    current_index = 0
            else:
                current_index = 0
        
        # Model selection with better spacing and accessibility
        st.markdown("### 🤖 AI Model Selection")
        selected_model = st.selectbox(
            "Choose the Claude model for question extraction",
            options=model_options,
            format_func=lambda x: AVAILABLE_CLAUDE_MODELS[x],
            index=current_index,
            disabled=extraction_in_progress,  # Disable during extraction
            key="model_selection",
            help="Different Claude models offer different capabilities:\n"
                 "• **Sonnet 4**: Latest model with optimal speed and performance balance\n"
                 "• **3.7 Sonnet**: Hybrid reasoning model with visible thinking steps",
            label_visibility="visible"
        )
        
        # Store the selected model
        state_manager.set_selected_extraction_model(selected_model)
        
        # Custom prompt for question extraction with better styling and accessibility
        st.markdown("### 📝 Custom Instructions")
        custom_prompt = st.text_area(
            "Custom Extraction Instructions (Optional)",
            value=state_manager.get_custom_extraction_prompt(),
            help="Provide specific instructions for how questions should be extracted and formatted",
            placeholder="Example: Extract only technical questions. Format each question with a brief context summary.",
            disabled=extraction_in_progress,  # Disable during extraction
            height=120,
            key="custom_prompt_input",
            label_visibility="visible"
        )
        
        # Store the custom prompt
        state_manager.set_custom_extraction_prompt(custom_prompt)
        
        # Extract button with better spacing and accessibility
        st.markdown("### 🔍 Question Extraction")
        if extraction_in_progress:
            st.markdown("""
            <div class="processing-status" role="status" aria-live="polite">
                🔄 Question extraction is currently in progress. Please wait...
            </div>
            """, unsafe_allow_html=True)
        elif st.button("🔍 Extract Questions", type="primary", key="extract_questions", 
                      help="Start the AI-powered question extraction process"):
            # Set extraction flag before starting
            st.session_state[SESSION_KEYS["EXTRACTION_IN_PROGRESS"]] = True
            _extract_questions(state_manager, doc_processor, extraction_service, custom_prompt)
    
    else:
        # Show extracted questions
        _show_extracted_questions(state_manager)
    
    # Navigation buttons with better spacing and accessibility
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back to Step 1", key="back_to_step1_nav", 
                    help="Return to file upload step"):
            state_manager.set_current_step(1)
            st.rerun()
    
    # Only show next button if questions are extracted
    if state_manager.has_questions():
        with col2:
            if st.button("Continue to Step 3 →", type="primary", key="continue_to_step3",
                        help="Proceed to answer generation step"):
                state_manager.set_current_step(3)
                st.rerun()
    
    # Close main content landmark
    st.markdown('</main>', unsafe_allow_html=True)
    
    logger.info("Step 2 (Extract) page rendered")


def _show_processing_status(extraction_method: str, model_name: str, start_time: float) -> None:
    """Show processing status with simple progress indicator.
    
    Args:
        extraction_method: The extraction method being used
        model_name: The model being used
        start_time: When processing started
    """
    elapsed_time = time.time() - start_time
    
    if extraction_method == "ai_extraction":
        # Get model display name
        model_display_name = AVAILABLE_CLAUDE_MODELS.get(model_name, model_name)
        
        # Simple animated dots (cycle through 1-3 dots)
        dots_count = (int(elapsed_time * 2) % 3) + 1
        dots = "." * dots_count
        
        # Show status with timeout info using custom styling and accessibility
        st.markdown(f"""
        <div class="processing-status" role="status" aria-live="polite" aria-label="Processing status">
            🤖 <strong>{model_display_name} is analyzing your document{dots}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Show progressively helpful tips with appropriate styling
        if elapsed_time > 180:  # 3 minutes
            st.warning("⚠️ **Still processing...** This is a complex document. The model will timeout after 5 minutes total.")
        elif elapsed_time > 120:  # 2 minutes
            st.info("💡 **Taking longer than usual.** Large documents with complex content can take up to 5 minutes to process.")
        elif elapsed_time > 60:  # 1 minute
            st.info("💡 **Still working...** Complex layouts or large files may take several minutes to analyze.")
    else:
        st.markdown(f"""
        <div class="processing-status" role="status" aria-live="polite" aria-label="Processing status">
            📊 <strong>Processing CSV content{dots}</strong>
        </div>
        """.format(dots="." * ((int(elapsed_time * 2) % 3) + 1)), unsafe_allow_html=True)


def _extract_questions(
    state_manager: StateManager,
    doc_processor: DocumentProcessor,
    extraction_service: QuestionExtractionService,
    custom_prompt: str
) -> None:
    """Extract questions from the uploaded file.
    
    Args:
        state_manager: State manager instance
        doc_processor: Document processor service
        extraction_service: Question extraction service
        custom_prompt: Custom extraction prompt
    """
    file_path = state_manager.get_file_path()
    
    # Check if file path is available
    if not file_path:
        st.error("No file path available. Please upload a file first.")
        st.session_state[SESSION_KEYS["EXTRACTION_IN_PROGRESS"]] = False
        return
    
    # Get the selected model
    selected_model = state_manager.get_selected_extraction_model()
    
    # Create placeholder for status updates
    status_placeholder = st.empty()
    
    try:
        with st.spinner("Extracting questions... This may take a few minutes."):
            # Show initial status
            status_placeholder.info("🔄 Preparing document for extraction...")
            
            # Prepare the file for extraction
            preparation = doc_processor.prepare_for_extraction(file_path)
            
            if not preparation["ready_for_extraction"]:
                status_placeholder.error("File preparation failed:")
                for error in preparation["errors"]:
                    st.error(f"• {error}")
                # Clear extraction flag on error
                st.session_state[SESSION_KEYS["EXTRACTION_IN_PROGRESS"]] = False
                return
            
            # Start processing time tracking
            start_time = time.time()
            
            # Show processing status
            _show_processing_status(
                preparation["extraction_method"], 
                selected_model, 
                start_time
            )
            
            # Extract questions using the appropriate method with selected model
            success, questions, extraction_info = extraction_service.extract_questions(
                content=preparation["content"],
                extraction_method=preparation["extraction_method"],
                custom_prompt=custom_prompt,
                metadata=preparation["metadata"],
                model_name=selected_model
            )
            
            # Clear status placeholder
            status_placeholder.empty()
            
            # Clear extraction flag regardless of success/failure
            st.session_state[SESSION_KEYS["EXTRACTION_IN_PROGRESS"]] = False
            
            if success and questions:
                # Store questions in state
                state_manager.set_questions(questions)
                
                # Create DataFrame for display
                df_input = pd.DataFrame(questions)
                state_manager.set_df_input(df_input)
                
                # Show success message with processing time
                processing_time = extraction_info.get("processing_time", 0)
                if processing_time > 0:
                    st.success(f"✅ {SUCCESS_MESSAGES['QUESTIONS_EXTRACTED'].format(count=len(questions))} (Processing time: {processing_time:.1f}s)")
                else:
                    st.success(SUCCESS_MESSAGES["QUESTIONS_EXTRACTED"].format(count=len(questions)))
                
                # Show method used for transparency with custom styling
                method_used = extraction_info.get("method", "unknown")
                model_used = extraction_info.get("model_used", selected_model)
                model_display_name = AVAILABLE_CLAUDE_MODELS.get(model_used, model_used)
                
                if method_used == "ai_extraction":
                    if processing_time > 10:
                        st.info(f"🔄 {model_display_name} took longer than usual, which may indicate it was warming up. Subsequent extractions should be faster.")
                    else:
                        st.info(f"🤖 Questions extracted using **{model_display_name}**")
                else:
                    st.info("📊 Questions extracted from CSV content")
                
                st.balloons()
                
                # Log extraction info
                logger.info(f"Extraction completed: {extraction_info}")
                
                # Rerun to show extracted questions
                st.rerun()
            else:
                # Extraction failed
                status_placeholder.error("❌ Question extraction failed.")
                if extraction_info.get("errors"):
                    for error in extraction_info["errors"]:
                        st.error(f"• {error}")
                else:
                    st.error("No questions could be extracted from the document.")
    except Exception as e:
        status_placeholder.error("❌ Unexpected error during extraction.")
        logger.error(f"Error in question extraction: {str(e)}")
        st.error(f"An unexpected error occurred during extraction: {str(e)}")
        if st.button("🔄 Try Again", type="primary"):
            st.rerun()


def _show_extracted_questions(state_manager: StateManager) -> None:
    """Show the extracted questions in an editable table.
    
    Args:
        state_manager: State manager instance
    """
    st.markdown("### 📋 Extracted Questions")
    
    questions = state_manager.get_questions()
    df = state_manager.get_df_input()
    
    if df is None or df.empty:
        st.error("No questions data available")
        return
    
    # Show extraction summary with custom styling and accessibility
    st.markdown(f"""
    <div class="file-processing-info" role="status" aria-live="polite">
        ✅ <strong>{len(questions)} questions extracted</strong> - Click on cells to edit, drag to select text for copying
    </div>
    """, unsafe_allow_html=True)
    
    # Import AgGrid for the table display
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
        
        # Configure AgGrid
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Configure columns based on the dataframe structure
        if "question" in df.columns:
            gb.configure_column("question", headerName="Question ID", width=120, editable=False)
        
        if "topic" in df.columns:
            gb.configure_column("topic", headerName="Topic", 
                               minWidth=200, wrapText=True, editable=True,
                               cellStyle={'whiteSpace': 'normal', 'backgroundColor': '#f8fafc'})
        
        if "sub_question" in df.columns:
            gb.configure_column("sub_question", headerName="Sub-Question ID", width=150, editable=False)
        
        if "text" in df.columns:
            gb.configure_column("text", headerName="Question Text", 
                               minWidth=400, wrapText=True, autoHeight=True, editable=True,
                               cellEditor="agLargeTextCellEditor",
                               cellEditorParams={"maxLength": 5000, "rows": 10, "cols": 80},
                               cellStyle={'whiteSpace': 'normal', 'backgroundColor': '#f0fdf4'})
        
        # Configure other columns
        for col in df.columns:
            if col not in ["question", "topic", "sub_question", "text"]:
                gb.configure_column(col, wrapText=True, editable=True, autoHeight=True)
        
        # Set grid options
        grid_options = gb.build()
        grid_options['defaultColDef'] = {
            'resizable': True,
            'sortable': True,
            'filter': True,
            'enableCellTextSelection': True,
            'wrapText': True,
            'autoHeight': True
        }
        
        # Display the grid with accessibility
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
            height=600,
            theme="streamlit",
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            key="questions_grid"
        )
        
        # Save changes automatically
        updated_df = grid_response["data"]
        if not df.equals(updated_df):
            state_manager.set_df_input(updated_df)
            state_manager.set_questions(updated_df.to_dict('records'))
            st.success("✅ Changes saved automatically!")
        
    except ImportError:
        st.warning("AgGrid not available - showing read-only table")
        st.dataframe(df, use_container_width=True, height=600, key="questions_dataframe")
    
    # Retry extraction button (only show if questions exist)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Re-extract Questions", key="re_extract_questions", 
                help="Clear current questions and start extraction again"):
        # Clear existing questions
        state_manager.clear_questions()
        st.rerun() 