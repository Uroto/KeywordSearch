from __future__ import annotations

import streamlit as st

from pages import research

st.set_page_config(page_title="キーワード調査", page_icon="🔎", layout="wide")

st.sidebar.caption("ローカル専用・Google Ads API 対応")

research.render()
