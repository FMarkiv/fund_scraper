import streamlit as st
from pathlib import Path
import re

st.set_page_config(layout="wide", page_title="Fund Newsletter")

# Load and process HTML
html_content = Path("newsletter_2026_01_5y.html").read_text(encoding="utf-8")

# Remove the header/nav section - keep only from <article> onwards
# Also remove the <header>...</header> block
html_content = re.sub(r'<header>.*?</header>\s*', '', html_content, flags=re.DOTALL)

# Remove the outer <main> tags but keep content
html_content = re.sub(r'<main>\s*', '', html_content)
html_content = re.sub(r'\s*</main>', '', html_content)

st.components.v1.html(html_content, height=2000, scrolling=True)
