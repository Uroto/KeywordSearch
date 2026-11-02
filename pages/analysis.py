from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render() -> None:
    st.title("検索数分析")
    results = st.session_state.get("results", [])
    if not results:
        st.info("キーワード調査画面で検索指標を取得すると、月別検索数を分析できます。")
        return
    keywords = [result["keyword"] for result in results if result.get("monthly_volumes")]
    selected = st.multiselect("比較するキーワード", keywords, default=keywords[: min(5, len(keywords))])
    rows = []
    for result in results:
        if result["keyword"] in selected:
            rows.extend({"月": item["month"], "検索数": item["volume"], "キーワード": result["keyword"]}
                        for item in result.get("monthly_volumes", []))
    if not rows:
        st.warning("グラフ表示するキーワードを選択してください。")
        return
    frame = pd.DataFrame(rows).sort_values("月")
    chart = px.line(frame, x="月", y="検索数", color="キーワード", markers=True,
                    title="月別検索ボリューム")
    chart.update_layout(legend_title_text="キーワード", yaxis_title="検索数")
    st.plotly_chart(chart, use_container_width=True)
    st.caption("Google Ads API の値は広告プランニング用の指標です。ダミーモード中は開発用の疑似値を表示します。")
