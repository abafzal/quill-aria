"""Step 3: Answer Generation page for ARIA application.

This module handles the answer generation functionality.
"""

import streamlit as st
import pandas as pd
from typing import Optional

from aria.ui.state_manager import StateManager
from aria.core.logging_config import get_logger
from aria.services import AnswerGenerationService
from aria.config.config import ERROR_MESSAGES, SUCCESS_MESSAGES, SESSION_KEYS

logger = get_logger(__name__)


def render_generate_page(state_manager: StateManager) -> None:
    """Render the answer generation page.
    
    Args:
        state_manager: State manager instance
    """
    st.header("Step 3: Generate Answers")
    
    # Check if questions have been extracted
    if not state_manager.has_questions():
        st.error(ERROR_MESSAGES["NO_QUESTIONS_AVAILABLE"])
        if st.button("← Back to Step 2"):
            state_manager.set_current_step(2)
            st.rerun()
        return
    
    # Check if generation is in progress
    generation_in_progress = st.session_state.get(SESSION_KEYS["GENERATION_IN_PROGRESS"], False)
    
    # If generation is in progress and we haven't completed yet, start processing
    if generation_in_progress and not state_manager.has_answers():
        _generate_answers_async(state_manager)
        return
    
    # Initialize service
    generation_service = AnswerGenerationService()
    
    # Show questions summary
    questions = state_manager.get_questions()
    st.info(f"Ready to generate answers for **{len(questions)} questions**")
    
    # Check if answers have already been generated
    if not state_manager.has_answers():
        # Show question selection and generation interface
        _show_generation_interface(state_manager, generation_service, questions)
    else:
        # Show generated answers
        _show_generated_answers(state_manager, generation_service)
    
    # Navigation buttons
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back to Step 2", disabled=generation_in_progress):
            state_manager.set_current_step(2)
            st.rerun()
    
    # Only show next button if answers are generated
    if state_manager.has_answers():
        with col2:
            if st.button("Continue to Step 4 →", type="primary", disabled=generation_in_progress):
                state_manager.set_current_step(4)
                st.rerun()
    
    logger.info("Step 3 (Generate) page rendered")


def _show_generation_interface(
    state_manager: StateManager,
    generation_service: AnswerGenerationService,
    questions: list
) -> None:
    """Show the question selection and generation interface.
    
    Args:
        state_manager: State manager instance
        generation_service: Answer generation service
        questions: List of questions
    """
    # Check if generation is in progress
    generation_in_progress = st.session_state.get(SESSION_KEYS["GENERATION_IN_PROGRESS"], False)
    
    # Show questions preview
    with st.expander("📋 Questions to Process", expanded=False):
        df = state_manager.get_df_input()
        if df is not None:
            st.dataframe(df, use_container_width=True)
        else:
            st.write("Questions data not available in DataFrame format")
    
    # Generation settings
    st.subheader("🎯 Answer Generation Settings")
    
    # Custom prompt input
    custom_prompt = st.text_area(
        "Custom Instructions for AI",
        value=state_manager.get_custom_prompt(),
        help="Customize how the AI should approach answering the questions",
        placeholder="Example: Focus on product capabilities released in the last 6 months. Include customer examples where possible.",
        disabled=generation_in_progress  # Disable during generation
    )
    
    # Store custom prompt
    state_manager.set_custom_prompt(custom_prompt)
    
    # Question selection
    st.subheader("📝 Question Selection")
    
    # Simple selection for now - in the future this could be more sophisticated
    select_all = st.checkbox("Select all questions for answer generation", value=True, disabled=generation_in_progress)
    
    if select_all:
        selected_questions = questions
        selected_count = len(questions)
        st.success(f"✅ {selected_count} questions selected")
    else:
        # Allow user to specify number of questions to process
        max_questions = len(questions)
        selected_count = st.number_input(
            "Number of questions to process", 
            min_value=1, 
            max_value=max_questions, 
            value=min(5, max_questions),  # Default to 5 or max available
            help="Select how many questions to process (useful for testing)",
            disabled=generation_in_progress  # Disable during generation
        )
        selected_questions = questions[:selected_count]
        st.info(f"📊 {selected_count} of {len(questions)} questions selected")
    
    # Generate answers button
    if generation_in_progress:
        st.info("🔄 Answer generation is currently in progress. Please wait...")
    elif st.button("🤖 Generate Answers", type="primary", disabled=selected_count == 0):
        # Set generation flag and store selected data before starting
        st.session_state[SESSION_KEYS["GENERATION_IN_PROGRESS"]] = True
        st.session_state["selected_questions_for_generation"] = selected_questions
        st.session_state["custom_prompt_for_generation"] = custom_prompt
        # Immediately rerun to update UI and show disabled button
        st.rerun()


def _generate_answers_async(state_manager: StateManager) -> None:
    """Handle asynchronous answer generation with proper flag management.
    
    Args:
        state_manager: State manager instance
    """
    # Get stored parameters
    selected_questions = st.session_state.get("selected_questions_for_generation", [])
    custom_prompt = st.session_state.get("custom_prompt_for_generation", "")
    
    if not selected_questions:
        st.error("No questions selected for generation")
        st.session_state[SESSION_KEYS["GENERATION_IN_PROGRESS"]] = False
        st.rerun()
        return
    
    # Show progress UI
    st.info("🔄 **Answer generation is in progress** - Please do not switch modes or navigate away")
    
    # Initialize service
    generation_service = AnswerGenerationService()
    
    # Call the actual generation function
    _generate_answers(state_manager, generation_service, selected_questions, custom_prompt)


def _generate_answers(
    state_manager: StateManager,
    generation_service: AnswerGenerationService,
    selected_questions: list,
    custom_prompt: str
) -> None:
    """Generate answers for the selected questions.
    
    Args:
        state_manager: State manager instance
        generation_service: Answer generation service
        selected_questions: List of selected questions
        custom_prompt: Custom prompt for generation
    """
    with st.spinner("Generating answers... This may take several minutes."):
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current: int, total: int, status: str) -> None:
            """Update progress display."""
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"{status} ({current}/{total})")
        
        try:
            # Generate answers using the service
            success, answers, generation_info = generation_service.generate_answers(
                questions=selected_questions,
                custom_prompt=custom_prompt,
                progress_callback=progress_callback
            )
            
            # Clear generation flag regardless of success/failure
            st.session_state[SESSION_KEYS["GENERATION_IN_PROGRESS"]] = False
            
            # Clean up temporary session state
            st.session_state.pop("selected_questions_for_generation", None)
            st.session_state.pop("custom_prompt_for_generation", None)
            
            if success and answers:
                # Store answers in state
                state_manager.set_generated_answers(answers)
                
                # Create DataFrame for display and export
                answers_df = pd.DataFrame(answers)
                state_manager.set_generated_answers_df(answers_df)
                
                # Complete progress
                progress_bar.progress(1.0)
                status_text.text("✅ Answer generation completed!")
                
                # Show success message
                st.success(SUCCESS_MESSAGES["ANSWERS_GENERATED"].format(count=len(answers)))
                st.balloons()
                
                # Log generation info
                logger.info(f"Generation completed: {generation_info}")
                
                # Rerun to show generated answers
                st.rerun()
                
            else:
                # Handle generation failure with specific error guidance
                progress_bar.progress(0)
                status_text.text("❌ Answer generation failed")
                
                if generation_info.get("errors"):
                    error_messages = generation_info["errors"]
                    model_name = generation_service.settings.models.answer_generation_model
                    
                    # Check for specific error patterns
                    has_auth_error = any("authentication" in str(error).lower() or "unauthorized" in str(error).lower() for error in error_messages)
                    has_503_error = any("503" in str(error) or "temporarily unavailable" in str(error).lower() for error in error_messages)
                    has_timeout = any("timeout" in str(error).lower() for error in error_messages)
                    
                    if has_auth_error:
                        st.error("🔐 **Authentication Error**")
                        st.error("Unable to authenticate with Databricks for answer generation.")
                        st.info("💡 **Next Steps**: Contact your administrator to verify your Databricks access credentials.")
                    elif has_503_error:
                        st.warning(f"⚠️ **Service Temporarily Unavailable**")
                        st.warning(f"{model_name} is currently unavailable. This usually resolves within a few minutes.")
                        st.info("💡 **Next Steps**: Wait a moment and try generating answers again.")
                    elif has_timeout:
                        st.warning(f"⚠️ **Request Timeout**")
                        st.warning(f"{model_name} request timed out. This may indicate high load.")
                        st.info("💡 **Next Steps**: Try again in a moment or reduce the number of questions to process.")
                    else:
                        st.error("❌ **Answer Generation Failed**")
                        st.error("Unable to generate answers for the questions.")
                        for error in error_messages:
                            st.error(f"• {error}")
                        st.info("💡 **Next Steps**: Try reducing the number of questions or contact support if the issue persists.")
                    
                    # Always show retry button for failed generation
                    if st.button("🔄 Try Again", type="primary"):
                        st.rerun()
                        
                else:
                    st.error("❌ **Answer Generation Failed**")
                    st.error("No answers could be generated for the questions.")
                    st.info("💡 **Next Steps**: Try reducing the number of questions or contact support if the issue persists.")
                    
                    # Show retry button
                    if st.button("🔄 Try Again", type="primary"):
                        st.rerun()
                
        except Exception as e:
            # Clear generation flag on exception
            st.session_state[SESSION_KEYS["GENERATION_IN_PROGRESS"]] = False
            
            # Clean up temporary session state
            st.session_state.pop("selected_questions_for_generation", None)
            st.session_state.pop("custom_prompt_for_generation", None)
            
            progress_bar.progress(0)
            status_text.text("❌ Unexpected error occurred")
            logger.error(f"Error in answer generation: {str(e)}")
            st.error("❌ **Unexpected Error**")
            st.error(f"An unexpected error occurred during answer generation: {str(e)}")
            st.info("💡 **Next Steps**: Try again or contact support if the issue persists.")
            
            # Show retry button
            if st.button("🔄 Try Again", type="primary"):
                st.rerun()


def _show_generated_answers(
    state_manager: StateManager,
    generation_service: AnswerGenerationService
) -> None:
    """Show the generated answers in an interactive table.
    
    Args:
        state_manager: State manager instance
        generation_service: Answer generation service
    """
    # Check if generation is in progress
    generation_in_progress = st.session_state.get(SESSION_KEYS["GENERATION_IN_PROGRESS"], False)
    
    st.subheader("🎉 Generated Answers")
    
    answers = state_manager.get_generated_answers()
    answers_df = state_manager.get_generated_answers_df()
    
    if not answers:
        st.error("No answers available")
        return
    
    st.success(f"✅ **{len(answers)} answers generated** - Review and edit as needed")
    
    # Show answers in an interactive format
    if answers_df is not None and not answers_df.empty:
        _show_answers_table(answers_df, state_manager)
    else:
        # Fallback to simple display
        _show_answers_simple(answers)
    
    # Regenerate button
    col1, col2 = st.columns([1, 3])
    with col1:
        if generation_in_progress:
            st.info("🔄 Regeneration in progress...")
        elif st.button("🔄 Regenerate Answers"):
            # Set generation flag and store regeneration data
            st.session_state[SESSION_KEYS["GENERATION_IN_PROGRESS"]] = True
            # Store the current questions and prompt for regeneration
            questions = state_manager.get_questions()
            custom_prompt = state_manager.get_custom_prompt()
            st.session_state["selected_questions_for_generation"] = questions
            st.session_state["custom_prompt_for_generation"] = custom_prompt
            # Clear existing answers
            state_manager.clear_answers()
            st.rerun()


def _show_answers_table(answers_df: pd.DataFrame, state_manager: StateManager) -> None:
    """Show answers in an interactive table format.
    
    Args:
        answers_df: DataFrame with answers
        state_manager: State manager instance
    """
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
        
        # Sort DataFrame by question_id in ascending order
        if "question_id" in answers_df.columns:
            # Handle both string and numeric question IDs
            try:
                # Try to sort numerically if possible
                answers_df_sorted = answers_df.copy()
                answers_df_sorted['sort_key'] = pd.to_numeric(answers_df_sorted['question_id'], errors='coerce')
                answers_df_sorted = answers_df_sorted.sort_values(['sort_key', 'question_id'], na_position='last')
                answers_df_sorted = answers_df_sorted.drop('sort_key', axis=1)
            except:
                # Fall back to string sorting
                answers_df_sorted = answers_df.sort_values('question_id')
        else:
            answers_df_sorted = answers_df.copy()
        
        # Configure AgGrid
        gb = GridOptionsBuilder.from_dataframe(answers_df_sorted)
        
        # Configure columns with better sizing
        if "question_id" in answers_df_sorted.columns:
            gb.configure_column("question_id", headerName="ID", width=80, editable=False, 
                               pinned='left', sort='asc')
        
        if "topic" in answers_df_sorted.columns:
            gb.configure_column("topic", headerName="Topic", 
                               width=140, wrapText=True, editable=False,
                               cellStyle={'backgroundColor': '#f5f9ff', 'fontWeight': '500'})
        
        if "question_text" in answers_df_sorted.columns:
            gb.configure_column("question_text", headerName="Question", 
                               width=250, wrapText=True, autoHeight=True, editable=False,
                               cellStyle={'backgroundColor': '#f7fbfe'})
        
        if "answer" in answers_df_sorted.columns:
            gb.configure_column("answer", headerName="Answer", 
                               flex=1, wrapText=True, autoHeight=True, editable=True,
                               cellEditor="agLargeTextCellEditor",
                               cellEditorParams={"maxLength": 10000, "rows": 6, "cols": 60},
                               cellStyle={'backgroundColor': '#f0f7ff', 'border-left': '3px solid #1976D2'})
        
        # Set grid options with better defaults
        grid_options = gb.build()
        grid_options['defaultColDef'] = {
            'resizable': True,
            'sortable': True,
            'filter': True,
            'enableCellTextSelection': True,
            'wrapText': True,
            'autoHeight': True
        }
        
        # Set initial sort on question_id
        if "question_id" in answers_df_sorted.columns:
            grid_options['columnDefs'][0]['sort'] = 'asc'
        
        # Display the grid with better sizing
        grid_response = AgGrid(
            answers_df_sorted,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
            height=600,
            theme="streamlit",
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.MODEL_CHANGED
        )
        
        # Save changes automatically
        updated_df = grid_response["data"]
        if not answers_df_sorted.equals(updated_df):
            # Update the stored answers
            state_manager.set_generated_answers_df(updated_df)
            # Also update the list format for backward compatibility
            updated_answers = updated_df.to_dict('records')
            state_manager.set_generated_answers(updated_answers)
            st.success("✅ Changes saved automatically!")
        
    except ImportError:
        st.warning("AgGrid not available - showing read-only table")
        # Sort DataFrame for fallback display too
        if "question_id" in answers_df.columns:
            try:
                # Try to sort numerically if possible
                answers_df_sorted = answers_df.copy()
                answers_df_sorted['sort_key'] = pd.to_numeric(answers_df_sorted['question_id'], errors='coerce')
                answers_df_sorted = answers_df_sorted.sort_values(['sort_key', 'question_id'], na_position='last')
                answers_df_sorted = answers_df_sorted.drop('sort_key', axis=1)
            except:
                # Fall back to string sorting
                answers_df_sorted = answers_df.sort_values('question_id')
        else:
            answers_df_sorted = answers_df.copy()
        
        st.dataframe(answers_df_sorted, use_container_width=True, height=600)


def _show_answers_simple(answers: list) -> None:
    """Show answers in a simple expandable format.
    
    Args:
        answers: List of answer dictionaries
    """
    for i, answer in enumerate(answers):
        question_text = answer.get('question_text', f"Question {i+1}")
        answer_text = answer.get('answer', 'No answer available')
        topic = answer.get('topic', 'Unknown')
        
        # Truncate question for display
        question_preview = question_text[:100] + "..." if len(question_text) > 100 else question_text
        
        with st.expander(f"Q{i+1}: {question_preview}"):
            st.write("**Topic:**", topic)
            st.write("**Question:**", question_text)
            st.write("**Answer:**")
            st.info(answer_text) 