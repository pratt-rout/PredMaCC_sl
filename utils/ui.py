"""Shared UI components."""

import streamlit as st

_CHAT_FAB_HTML = """
<style>
.chat-fab {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: #1f77b4;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    cursor: pointer;
    z-index: 9999;
    text-decoration: none;
    transition: background 0.2s;
}
.chat-fab:hover {
    background: #125a8a;
    color: white;
    text-decoration: none;
}
</style>
<a class="chat-fab" href="/AI_Assistant" target="_self" title="Open AI Assistant">
    💬
</a>
"""


def chat_fab():
    """Render floating AI Assistant button in the bottom-right corner."""
    st.markdown(_CHAT_FAB_HTML, unsafe_allow_html=True)
