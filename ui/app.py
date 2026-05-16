"""Streamlit UI for NL2SQL RAG system.

Usage:
    streamlit run ui/app.py
"""

import os
import sys

# Ensure project root is on sys.path so 'ui', 'ingestion', etc. are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="NL2SQL RAG",
    page_icon="",
    layout="wide",
)

from ui.components.chat_panel import render_chat
from ui.components.sidebar import render_sidebar
from ui.utils.state import init_session_state

init_session_state()
render_sidebar()
render_chat()
