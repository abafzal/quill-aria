"""Step 4: Download & Export page for ARIA application.

This module handles the final review and export functionality.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional

from aria.ui.state_manager import StateManager
from aria.core.logging_config import get_logger
from aria.config.config import ERROR_MESSAGES, SUCCESS_MESSAGES, EXPORT_EXTENSIONS

logger = get_logger(__name__)


def render_download_page(state_manager: StateManager) -> None:
    """Render the download and export page.
    
    Args:
        state_manager: State manager instance
    """
    st.header("Step 4: Review & Download")
    
    # Check if answers have been generated
    if not state_manager.has_answers():
        st.error(ERROR_MESSAGES["NO_ANSWERS_AVAILABLE"])
        if st.button("← Back to Step 3"):
            state_manager.set_current_step(3)
            st.rerun()
        return
    
    # Get answers data
    answers = state_manager.get_generated_answers()
    answers_df = state_manager.get_generated_answers_df()
    
    # Show summary
    st.success(f"🎉 **Process Complete!** {len(answers)} answers ready for export")
    
    # Show summary statistics
    _show_summary_stats(answers, answers_df)
    
    # Final review section
    _show_final_review(answers_df, state_manager)
    
    # Export section
    _show_export_options(answers_df, state_manager)
    
    # Navigation buttons
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back to Step 3"):
            state_manager.set_current_step(3)
            st.rerun()
    
    with col2:
        if st.button("🔄 Start New Process", type="secondary"):
            # Reset the entire process
            state_manager.reset_session()
            state_manager.set_current_step(1)
            st.rerun()
    
    logger.info("Step 4 (Download) page rendered")


def _show_summary_stats(answers: list, answers_df: Optional[pd.DataFrame]) -> None:
    """Show summary statistics about the generated answers.
    
    Args:
        answers: List of answer dictionaries
        answers_df: DataFrame with answers (optional)
    """
    with st.expander("📊 Summary Statistics", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Questions", len(answers))
        
        with col2:
            # Count unique topics
            topics = set(answer.get('topic', 'Unknown') for answer in answers)
            st.metric("Topics Covered", len(topics))
        
        with col3:
            # Calculate average answer length
            answer_lengths = [len(answer.get('answer', '')) for answer in answers]
            avg_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
            st.metric("Avg Answer Length", f"{avg_length:.0f} chars")
        
        with col4:
            # Show completion time if available
            execution_time = st.session_state.get('execution_time', 0)
            if execution_time > 0:
                st.metric("Processing Time", f"{execution_time:.1f}s")
            else:
                st.metric("Status", "✅ Complete")
        
        # Show topic breakdown
        if len(topics) > 1:
            st.write("**Topics covered:**")
            topic_counts = {}
            for answer in answers:
                topic = answer.get('topic', 'Unknown')
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Display as columns
            topic_cols = st.columns(min(len(topic_counts), 4))
            for i, (topic, count) in enumerate(topic_counts.items()):
                with topic_cols[i % len(topic_cols)]:
                    st.write(f"• **{topic}**: {count} questions")


def _show_final_review(answers_df: Optional[pd.DataFrame], state_manager: StateManager) -> None:
    """Show the final review interface for answers.
    
    Args:
        answers_df: DataFrame with answers
        state_manager: State manager instance
    """
    st.subheader("📋 Final Review")
    
    if answers_df is None or answers_df.empty:
        st.error("No answers data available for review")
        return
    
    # Show review options
    review_mode = st.radio(
        "Review Mode",
        ["Summary View", "Detailed Table", "Export Preview"],
        horizontal=True
    )
    
    if review_mode == "Summary View":
        _show_summary_view(answers_df)
    elif review_mode == "Detailed Table":
        _show_detailed_table(answers_df, state_manager)
    else:  # Export Preview
        _show_export_preview(answers_df)


def _show_summary_view(answers_df: pd.DataFrame) -> None:
    """Show a summary view of the answers.
    
    Args:
        answers_df: DataFrame with answers
    """
    st.info("📖 **Summary View** - Quick overview of all answers")
    
    # Group by topic if available
    if 'topic' in answers_df.columns:
        topics = answers_df['topic'].unique()
        
        for topic in topics:
            topic_df = answers_df[answers_df['topic'] == topic]
            
            with st.expander(f"📁 {topic} ({len(topic_df)} questions)", expanded=False):
                for _, row in topic_df.iterrows():
                    question_text = row.get('question_text', 'No question text') or 'No question text'
                    answer_text = row.get('answer', 'No answer') or 'No answer'
                    
                    # Truncate for summary
                    question_preview = question_text[:100] + "..." if len(question_text) > 100 else question_text
                    answer_preview = answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
                    
                    st.write(f"**Q:** {question_preview}")
                    st.write(f"**A:** {answer_preview}")
                    st.divider()
    else:
        # Show without topic grouping
        for i, (idx, row) in enumerate(answers_df.iterrows()):
            question_text = row.get('question_text', f'Question {i+1}') or f'Question {i+1}'
            answer_text = row.get('answer', 'No answer') or 'No answer'
            
            question_preview = question_text[:100] + "..." if len(question_text) > 100 else question_text
            
            with st.expander(f"Q{i+1}: {question_preview}"):
                st.write("**Question:**", question_text)
                st.write("**Answer:**")
                st.info(answer_text)


def _show_detailed_table(answers_df: pd.DataFrame, state_manager: StateManager) -> None:
    """Show a detailed editable table of answers.
    
    Args:
        answers_df: DataFrame with answers
        state_manager: State manager instance
    """
    st.info("📝 **Detailed Table** - Make final edits before export")
    
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
        
        # Configure AgGrid for final review
        gb = GridOptionsBuilder.from_dataframe(answers_df_sorted)
        
        # Configure columns with better sizing
        if "question_id" in answers_df_sorted.columns:
            gb.configure_column("question_id", headerName="ID", width=80, editable=False,
                               pinned='left', sort='asc')
        
        if "topic" in answers_df_sorted.columns:
            gb.configure_column("topic", headerName="Topic", 
                               width=140, wrapText=True, editable=True,
                               cellStyle={'backgroundColor': '#e8f5e8'})
        
        if "question_text" in answers_df_sorted.columns:
            gb.configure_column("question_text", headerName="Question", 
                               width=250, wrapText=True, autoHeight=True, editable=False,
                               cellStyle={'backgroundColor': '#f0f8ff'})
        
        if "answer" in answers_df_sorted.columns:
            gb.configure_column("answer", headerName="Answer", 
                               flex=1, wrapText=True, autoHeight=True, editable=True,
                               cellEditor="agLargeTextCellEditor",
                               cellEditorParams={"maxLength": 10000, "rows": 6, "cols": 60},
                               cellStyle={'backgroundColor': '#fff8e1', 'border-left': '3px solid #ff9800'})
        
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
            height=500,
            theme="streamlit",
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.MODEL_CHANGED
        )
        
        # Save changes automatically
        updated_df = grid_response["data"]
        if not answers_df_sorted.equals(updated_df):
            # Update the stored answers
            state_manager.set_generated_answers_df(updated_df)
            state_manager.set_export_answers_df(updated_df)
            # Also update the list format
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
        
        st.dataframe(answers_df_sorted, use_container_width=True, height=500)


def _show_export_preview(answers_df: pd.DataFrame) -> None:
    """Show a preview of how the export will look.
    
    Args:
        answers_df: DataFrame with answers
    """
    st.info("👁️ **Export Preview** - How your data will appear in the exported file")
    
    # Sort DataFrame by question_id in ascending order for preview
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
    
    # Show the dataframe as it will be exported
    st.dataframe(answers_df_sorted, use_container_width=True, height=400)
    
    # Show column information
    st.write("**Export will include these columns:**")
    for col in answers_df_sorted.columns:
        st.write(f"• **{col}**: {answers_df_sorted[col].dtype}")


def _show_export_options(answers_df: pd.DataFrame, state_manager: StateManager) -> None:
    """Show export options and download button.
    
    Args:
        answers_df: DataFrame with answers
        state_manager: State manager instance
    """
    st.subheader("💾 Export Options")
    
    # Prepare export data
    export_df = answers_df.copy()
    state_manager.set_export_answers_df(export_df)
    
    # File naming and format selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Generate default filename only if not already set in session state
        if 'export_filename' not in st.session_state:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rfi_name = state_manager.get_rfi_name() or "quill_export"
            default_filename = f"{rfi_name}_answers_{timestamp}"
            st.session_state['export_filename'] = default_filename
        
        filename = st.text_input(
            "Export Filename (without extension)",
            value=st.session_state['export_filename'],
            help="Enter the filename for your export (extension will be added automatically)",
            key="filename_input"
        )
        
        # Update session state when user changes the filename
        if filename and filename != st.session_state['export_filename']:
            st.session_state['export_filename'] = filename
        
        # Ensure filename is not None
        final_filename = filename or st.session_state['export_filename']
        state_manager.set_output_file_name(final_filename)
    
    with col2:
        export_format = st.selectbox(
            "Export Format",
            ["CSV", "HTML"],
            help="Choose the format for your exported file"
        )
    
    # Single download button that triggers the appropriate download
    try:
        if export_format == "CSV":
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV File",
                data=csv_data,
                file_name=f"{filename}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:  # HTML
            # Create a nicely formatted HTML table
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Quill Export - {filename}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #1976D2; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #f5f5f5; font-weight: bold; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .question {{ background-color: #e3f2fd; }}
                    .answer {{ background-color: #fff3e0; }}
                    .topic {{ background-color: #e8f5e8; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>Quill Export Results</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><strong>Total Questions:</strong> {len(export_df)}</p>
                
                {export_df.to_html(escape=False, classes='table table-striped', table_id='results-table')}
            </body>
            </html>
            """
            
            st.download_button(
                label="📥 Download HTML File",
                data=html_content,
                file_name=f"{filename}.html",
                mime="text/html",
                type="primary",
                use_container_width=True
            )
    except Exception as e:
        logger.error(f"Error generating {export_format} file: {str(e)}")
        st.error(f"Error generating {export_format} file: {str(e)}")


 