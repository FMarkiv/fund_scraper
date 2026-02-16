import streamlit as st
from pathlib import Path

st.set_page_config(layout="wide", page_title="Fund Newsletter")

html_content = Path("newsletter_2026_01_5y.html").read_text(encoding="utf-8")
st.components.v1.html(html_content, height=2000, scrolling=True)
