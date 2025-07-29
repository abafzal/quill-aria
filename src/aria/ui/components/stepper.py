"""Stepper component for ARIA application.

This module provides a visual progress stepper component to show
the current step in the processing workflow.
"""

import streamlit as st
from typing import List, Dict, Any
from aria.core.types import ProcessingStep
from aria.core.logging_config import log_info


def render_stepper(current_step: int) -> None:
    """Render the progress stepper component.
    
    Args:
        current_step: Current step number (1-4)
    """
    steps = _get_step_definitions()
    
    # Add stepper-specific CSS
    _load_stepper_css()
    
    # Add a spacer before stepper
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    
    # Create progress bar
    _render_progress_bar(current_step, len(steps))
    
    # Create step columns
    _render_step_circles(steps, current_step)
    
    log_info(f"Stepper rendered for step {current_step}")


def _get_step_definitions() -> List[Dict[str, Any]]:
    """Get step definitions for the stepper.
    
    Returns:
        List of step definitions
    """
    return [
        {"number": 1, "label": "Upload"},
        {"number": 2, "label": "Extract & Review Questions"},
        {"number": 3, "label": "Generate Answers"},
        {"number": 4, "label": "Review & Download"}
    ]


def _load_stepper_css() -> None:
    """Load CSS specific to the stepper component."""
    stepper_css = """
    <style>
    .stepper-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        margin: 5px 0 10px 0; 
        width: 100%;
    }
    .progress-bar {
        position: absolute;
        height: 4px;
        background-color: #E0E0E0;
        top: 20px;
        left: 5%;
        right: 5%;
        z-index: 1;
    }
    .progress-fill {
        position: absolute;
        height: 4px;
        background-color: #FF8C00;
        top: 20px;
        left: 5%;
        z-index: 1;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 2;
        position: relative;
    }
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 8px;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .step-label {
        text-align: center;
        font-size: 14px;
    }
    </style>
    """
    st.markdown(stepper_css, unsafe_allow_html=True)


def _render_progress_bar(current_step: int, total_steps: int) -> None:
    """Render the progress bar.
    
    Args:
        current_step: Current step number
        total_steps: Total number of steps
    """
    # Calculate progress percentage
    if current_step == 1:
        progress_value = 0.0
    elif current_step > total_steps:
        progress_value = 1.0
    else:
        progress_value = (current_step - 1) / (total_steps - 1)
    
    # Add progress container with reduced spacing
    progress_container = st.container()
    with progress_container:
        st.markdown("<div style='margin-top: -10px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
        st.progress(progress_value)


def _render_step_circles(steps: List[Dict[str, Any]], current_step: int) -> None:
    """Render the step circles and labels.
    
    Args:
        steps: List of step definitions
        current_step: Current step number
    """
    cols = st.columns(len(steps))
    
    for i, step in enumerate(steps):
        with cols[i]:
            step_status = _get_step_status(step["number"], current_step)
            _render_single_step(step, step_status)


def _get_step_status(step_number: int, current_step: int) -> str:
    """Determine the status of a step.
    
    Args:
        step_number: The step number to check
        current_step: Current step number
        
    Returns:
        Step status: 'completed', 'current', or 'future'
    """
    if step_number < current_step:
        return 'completed'
    elif step_number == current_step:
        return 'current'
    else:
        return 'future'


def _render_single_step(step: Dict[str, Any], status: str) -> None:
    """Render a single step circle and label.
    
    Args:
        step: Step definition
        status: Step status ('completed', 'current', 'future')
    """
    step_number = step["number"]
    step_label = step["label"]
    
    if status == 'completed':
        # Completed step
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #FF8C00; color: white; 
                 border: 1px solid #FF8C00; display: flex; align-items: center; justify-content: center; 
                 margin-bottom: 8px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                ✓
            </div>
            <div style="color: #666666; font-weight: normal; font-size: 14px;">
                {step_label}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    elif status == 'current':
        # Current step
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #FF8C00; color: white; 
                 border: 1px solid #FF8C00; display: flex; align-items: center; justify-content: center; 
                 margin-bottom: 8px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                {step_number}
            </div>
            <div style="color: #333333; font-weight: bold; font-size: 14px;">
                {step_label}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Future step
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: white; color: #555555; 
                 border: 1px solid #cccccc; display: flex; align-items: center; justify-content: center; 
                 margin-bottom: 8px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                {step_number}
            </div>
            <div style="color: #666666; font-weight: normal; font-size: 14px;">
                {step_label}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_navigation_buttons(current_step: int, state_manager) -> None:
    """Render navigation buttons for moving between steps.
    
    Args:
        current_step: Current step number
        state_manager: State manager instance
    """
    nav_col1, nav_col2 = st.columns([1, 3])
    
    with nav_col1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Back button (disabled on first step)
            if current_step > 1:
                if st.button("← Back", key=f"back_btn_step_{current_step}"):
                    state_manager.set_current_step(current_step - 1)
                    st.rerun()
        
        with col2:
            # Next button (enabled based on step completion)
            next_enabled = _is_next_step_available(current_step, state_manager)
            next_label = "Next →" if current_step < 4 else "Finish"
            
            if st.button(next_label, key=f"next_btn_step_{current_step}", disabled=not next_enabled):
                if current_step < 4:
                    state_manager.set_current_step(current_step + 1)
                    st.rerun()
                else:
                    # On final step, could trigger completion actions
                    st.success("Process completed!")


def _is_next_step_available(current_step: int, state_manager) -> bool:
    """Check if the next step is available based on current progress.
    
    Args:
        current_step: Current step number
        state_manager: State manager instance
        
    Returns:
        True if next step is available, False otherwise
    """
    if current_step == 1:
        return state_manager.has_uploaded_file()
    elif current_step == 2:
        return state_manager.has_questions()
    elif current_step == 3:
        return state_manager.has_answers()
    elif current_step == 4:
        return not state_manager.get_export_data().empty
    
    return False


def render_compact_stepper(current_step: int) -> None:
    """Render a compact version of the stepper for narrow layouts.
    
    Args:
        current_step: Current step number
    """
    steps = _get_step_definitions()
    
    # Compact stepper CSS
    compact_css = """
    <style>
    .compact-stepper {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 10px 0;
        padding: 8px 16px;
        background-color: #f8f9fa;
        border-radius: 20px;
        border: 1px solid #e0e0e0;
    }
    .compact-step {
        margin: 0 8px;
        font-size: 14px;
        font-weight: 500;
    }
    .compact-step.current {
        color: #FF8C00;
        font-weight: bold;
    }
    .compact-step.completed {
        color: #4CAF50;
    }
    .compact-step.future {
        color: #999999;
    }
    </style>
    """
    st.markdown(compact_css, unsafe_allow_html=True)
    
    # Render compact stepper
    step_html = '<div class="compact-stepper">'
    for i, step in enumerate(steps):
        status = _get_step_status(step["number"], current_step)
        step_html += f'<span class="compact-step {status}">{step["number"]}. {step["label"]}</span>'
        if i < len(steps) - 1:
            step_html += '<span style="margin: 0 4px; color: #ccc;">→</span>'
    step_html += '</div>'
    
    st.markdown(step_html, unsafe_allow_html=True) 