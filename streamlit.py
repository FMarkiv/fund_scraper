import streamlit as st
from pathlib import Path
import re

st.set_page_config(layout="wide", page_title="Fund Newsletter", initial_sidebar_state="collapsed")

# Hide Streamlit's default padding, header, and sidebar
st.markdown("""
<style>
    /* Remove Streamlit branding and padding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    .block-container {
        padding-top: 0;
        padding-bottom: 0;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Make iframe take full height without scrollbar */
    iframe {
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Load and process HTML
html_content = Path("newsletter_2026_02_v2.html").read_text(encoding="utf-8")

# Remove the header/nav section
html_content = re.sub(r'<header>.*?</header>\s*', '', html_content, flags=re.DOTALL)

# Remove the outer <main> tags but keep content
html_content = re.sub(r'<main>\s*', '', html_content)
html_content = re.sub(r'\s*</main>', '', html_content)

# Use a very tall height so iframe doesn't scroll internally
st.components.v1.html(html_content, height=30000, scrolling=False)
