import streamlit as st
from pathlib import Path
import re

st.set_page_config(layout="wide", page_title="Fund Newsletter")

# Available newsletters (newest first)
NEWSLETTERS = {
    "February 2026": "newsletter_2026_02_v2.html",
    "January 2026": "newsletter_2026_01.html",
}

# Month selector in sidebar
with st.sidebar:
    st.title("DBFS Fund Newsletter")
    selected_month = st.selectbox("Select month", list(NEWSLETTERS.keys()))

# Hide Streamlit's default padding and header
st.markdown("""
<style>
    /* Remove Streamlit branding and padding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
html_file = NEWSLETTERS[selected_month]
html_content = Path(html_file).read_text(encoding="utf-8")

# Remove the header/nav section
html_content = re.sub(r'<header>.*?</header>\s*', '', html_content, flags=re.DOTALL)

# Remove the outer <main> tags but keep content
html_content = re.sub(r'<main>\s*', '', html_content)
html_content = re.sub(r'\s*</main>', '', html_content)

# Use a very tall height so iframe doesn't scroll internally
st.components.v1.html(html_content, height=15000, scrolling=False)
