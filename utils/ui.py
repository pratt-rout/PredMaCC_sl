"""Shared UI components."""

import streamlit as st


def tall_sidebar_nav(height: str = "70vh"):
    """Fix the sidebar page-list area to `height`, pushing the divider and widgets below it down."""
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNav"] > ul,
        [data-testid="stSidebarNavItems"] {{
            min-height: {height} !important;
            max-height: {height} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
