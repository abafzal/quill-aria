"""CSS styling for ARIA application.

This module provides centralized CSS styling for the Streamlit application,
extracted from the original helpers.py file for better organization.
"""

import streamlit as st
from aria.core.logging_config import log_info


def load_custom_css() -> None:
    """Load custom CSS styling for the application.
    
    This function applies comprehensive styling including:
    - Component styling (buttons, inputs, toggles)
    - AgGrid table styling
    - Navigation and stepper styling
    - Color scheme and typography
    """
    css_content = _get_main_css()
    st.markdown(css_content, unsafe_allow_html=True)
    log_info("Custom CSS loaded successfully")


def load_header_css() -> None:
    """Load CSS for the application header."""
    header_css = """
    <style>
    /* Fully hide Streamlit's system UI */
    header, footer {visibility: hidden;}

    /* Restore default backgrounds and ensure readable text */
    html, body, .stApp, .stMarkdown, .stTextInput label, .stTextArea label {
        color: #333333 !important;
    }

    /* Create a fixed header bar manually */
    #customHeader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 60px;
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding: 0 1.5rem;
        z-index: 1000;
        font-family: 'DM Sans', sans-serif;
    }

    #customHeader h1 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1E88E5;
        margin: 0;
    }
    </style>
    """
    st.markdown(header_css, unsafe_allow_html=True)


def load_sidebar_css() -> None:
    """Load CSS for the sidebar styling."""
    sidebar_css = """
    <style>
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eaecef;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #1E88E5;
        font-size: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #eaecef;
        margin-top: 0.5rem;
    }
    [data-testid="stSidebar"] .stAlert {
        border: none;
        background-color: #e3f2fd;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)


def _get_main_css() -> str:
    """Get the main CSS content.
    
    Returns:
        CSS content as string
    """
    return """
    <style>
    /* Force all toggle text to black+bold */
    [data-testid="stToggle"] label, 
    [data-testid="stToggle"] label * {
      color: #000 !important;
      font-weight: 700 !important;
    }
    
    /* Ensure checkbox labels are visible */
    [data-testid="stCheckbox"] label, 
    [data-testid="stCheckbox"] label p {
      color: #000 !important;
      font-weight: 700 !important;
      font-size: 1rem !important;
    }
    
    /* Give the track a heavy border */
    [data-testid="stToggle"] {
      border: 2px solid #555 !important;
      padding: 4px 8px !important;
      border-radius: 20px !important;
    }
    
    /* Button styling */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #FF8C00;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #E07000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Back button styling - smaller and blue */
    .back-button button {
        background-color: #1976D2 !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
    }
    .back-button button:hover {
        background-color: #1565C0 !important;
    }
    
    /* AgGrid custom styling */
    .ag-theme-streamlit {
        --ag-background-color: white !important;
        --ag-foreground-color: #333333 !important;
        --ag-header-background-color: #f0f0f0 !important;
        --ag-header-foreground-color: #505050 !important;
        --ag-header-font-weight: 600;
        --ag-row-hover-color: #f8f9fa;
        --ag-selected-row-background-color: rgba(25, 118, 210, 0.1);
        --ag-font-family: sans-serif;
        --ag-font-size: 14px;
        --ag-cell-horizontal-border: 1px solid #e0e0e0;
        --ag-header-column-separator-color: #e0e0e0;
        --ag-borders: none;
        --ag-border-radius: 4px;
        --ag-row-border-color: #f0f0f0;
        --ag-odd-row-background-color: #f9f9f9 !important;
        --ag-even-row-background-color: #ffffff !important;
        --ag-alpine-active-color: #1976D2;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        overflow: hidden;
    }
    
    /* Force consistent cell styling */
    .ag-theme-streamlit .ag-cell {
        color: #333333 !important;
        background-color: inherit !important;
        user-select: text !important;
        -webkit-user-select: text !important;
        white-space: normal !important;
        line-height: 1.5 !important;
        padding: 8px 15px !important;
    }
    
    /* Consistent header styling */
    .ag-theme-streamlit .ag-header-cell {
        background-color: #f0f0f0 !important;
        color: #505050 !important;
        font-weight: bold !important;
        border-bottom: 1px solid #e0e0e0 !important;
    }
    
    /* Consistent row styling with thin borders */
    .ag-theme-streamlit .ag-row {
        border-bottom: 1px solid #f0f0f0 !important;
    }
    
    /* Question ID and Sub-Question ID styling */
    .ag-theme-streamlit .ag-cell[col-id="question"],
    .ag-theme-streamlit .ag-cell[col-id="sub_question"] {
        color: #666666 !important;
    }
    
    /* Card styling with subtle borders */
    .streamlit-expanderHeader, div.stDataFrame {
        background-color: white;
        border: 1px solid #e6e6e6;
        border-radius: 5px;
    }
    
    /* Fix notification boxes to ensure text is black */
    div.stAlert > div {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    /* Specifically target each notification type */
    div[data-baseweb="notification"] {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    /* Make all alert boxes use the same blue color scheme with darker text */
    div[data-testid="stInfoBox"],
    div[data-testid="stSuccessBox"],
    div[data-testid="stWarningBox"],
    div[data-testid="stErrorBox"] {
        background-color: #e8f4f8 !important;
        border-color: #8cbfd4 !important;
    }
    
    /* Make all alert boxes text darker and bolder */
    div[data-testid="stInfoBox"] p,
    div[data-testid="stSuccessBox"] p,
    div[data-testid="stWarningBox"] p,
    div[data-testid="stErrorBox"] p {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    /* Make all alert box icons use the same blue color */
    div[data-testid="stInfoBox"] svg,
    div[data-testid="stSuccessBox"] svg,
    div[data-testid="stWarningBox"] svg,
    div[data-testid="stErrorBox"] svg {
        fill: #3498db !important;
    }
    
    /* Style input text fields with blue border and background */
    input[type="text"], 
    textarea, 
    [data-baseweb="input"], 
    [data-baseweb="textarea"],
    [data-baseweb="select"] > div,
    [data-baseweb="select"] div {
        border-color: #8cbfd4 !important;
        background-color: #f7fbfe !important;
        color: black !important;
    }
    
    /* Ensure text area content is black */
    textarea, .stTextArea textarea, [data-baseweb="textarea"] textarea {
        color: black !important;
    }
    
    /* Ensure dataframe text is black */
    .stDataFrame div, .stDataFrame span, .stTable div, .stTable span {
        color: black !important;
    }
    
    /* Navigation row and button styling */
    .navigation-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 20px 0;
        padding: 10px 0;
        width: 100%;
    }
    
    /* Button container styling */
    .button-container {
        display: flex;
        gap: 10px;
        margin: 20px 0;
    }
    
    /* Navigation buttons */
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
        width: 100%;
    }
    .navigation-buttons .left-button {
        flex: 0 0 auto;
    }
    .navigation-buttons .right-button {
        flex: 0 0 auto;
        margin-left: auto;
    }
    
    /* Navigation bar */
    .navigation-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
        width: 100%;
    }
    
    /* Stepper component styling */
    .step-container {
        display: flex;
        justify-content: space-between;
        padding: 0;
        margin-bottom: 40px;
        position: relative;
    }
    .step-container::before {
        content: '';
        position: absolute;
        top: 15px;
        left: 0;
        right: 0;
        height: 2px;
        background: #e0e0e0;
        z-index: 1;
    }
    .step {
        position: relative;
        z-index: 2;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: white;
        border: 2px solid #e0e0e0;
        display: flex;
        justify-content: center;
        align-items: center;
        color: #757575;
        font-weight: bold;
        margin: 0 auto 10px;
    }
    .step.active .step-circle {
        background-color: #1976D2;
        border-color: #1976D2;
        color: white;
    }
    .step.completed .step-circle {
        background-color: #4CAF50;
        border-color: #4CAF50;
        color: white;
    }
    .step-title {
        font-size: 12px;
        color: #333333;
        text-align: center;
        font-weight: 500;
    }
    .step.active .step-title {
        color: #1976D2;
        font-weight: bold;
    }
    .step.completed .step-title {
        color: #4CAF50;
        font-weight: 500;
    }
    
    /* Custom link button */
    a.button {
        display: inline-block;
        background-color: #FF8C00;
        color: white;
        text-decoration: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 20px;
        transition: all 0.3s ease;
    }
    a.button:hover {
        background-color: #E07000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-decoration: none;
    }

    /* Restore global text color for readability */
    body, .stApp, .main, section[data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #212121 !important;
    }

    /* Style text input labels */
    [data-testid="stTextInput"] label {
        color: #212121 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    /* Ensure default background stays light without washing out text */
    body {
        background-color: #ffffff !important;
    }

    /* Global text improvements */
    body, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, span, div, li, label {
        color: #111111 !important;
    }

    /* Step containers with subtle backgrounds */
    .step-container {
        background-color: white;
        border-radius: 5px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* Information boxes */
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976D2;
        padding: 15px;
        margin: 15px 0;
        color: #111111;
    }

    /* Success messages */
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin: 15px 0;
        color: #111111;
    }

    /* Step 4 specific improvements */
    .step4-content {
        color: #111111 !important;
        background-color: #f8f9fa !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        border-radius: 5px !important;
        border-left: 4px solid #1976D2 !important;
    }

    /* Table/Grid improvements */
    .ag-theme-streamlit .ag-cell {
        color: #111111 !important;
    }
    </style>
    """


def apply_step_specific_css(step: int) -> None:
    """Apply step-specific CSS styling.
    
    Args:
        step: Current step number
    """
    if step == 4:
        # Step 4 specific styling
        step4_css = """
        <style>
        /* Simple fixes for text visibility in Step 4 */
        .step4-content {
            color: #333333 !important;
            background-color: white !important;
            padding: 8px;
            margin: 4px 0;
            border-radius: 4px;
        }
        .step4-section {
            margin-top: 20px;
            margin-bottom: 10px;
        }
        </style>
        """
        st.markdown(step4_css, unsafe_allow_html=True)


def load_font_imports() -> None:
    """Load Google Fonts imports."""
    font_css = """
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    """
    st.markdown(font_css, unsafe_allow_html=True) 