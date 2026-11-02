from __future__ import annotations

import streamlit as st

from pages import analysis, research, settings

st.set_page_config(page_title="創作ライフ | キーワード調査", page_icon="🔎", layout="wide")

st.sidebar.title("創作ライフ")
page = st.sidebar.radio("メニュー", ["キーワード調査", "検索数分析", "設定"])
st.sidebar.caption("ローカル専用・Google Ads API 対応")

if page == "キーワード調査":
    research.render()
elif page == "検索数分析":
    analysis.render()
else:
    settings.render()
