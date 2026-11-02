from __future__ import annotations

import pandas as pd
import streamlit as st

from config import CACHE_FILE, get_settings
from services.cache import JsonCache
from services.export import results_frame, to_excel_csv, keywords_from_csv
from services.google_ads import create_provider
from services.keyword import KeywordResearchService, normalize_keywords


def _service() -> KeywordResearchService:
    settings = get_settings()
    return KeywordResearchService(create_provider(settings), JsonCache(CACHE_FILE), settings)


def _filtered_results(results: list[dict]) -> pd.DataFrame:
    frame = results_frame(results)
    if frame.empty:
        return frame
    text = st.text_input("キーワードで絞り込み")
    competitions = st.multiselect("競合性", ["低", "中", "高", "不明"], default=["低", "中", "高", "不明"])
    min_volume, max_volume = st.slider("月間平均検索ボリューム", 0, int(frame["月間平均検索ボリューム"].max()), (0, int(frame["月間平均検索ボリューム"].max())))
    filtered = frame[
        frame["競合性"].isin(competitions)
        & frame["月間平均検索ボリューム"].between(min_volume, max_volume)
        & frame["キーワード"].str.contains(text, case=False, na=False)
    ]
    return filtered.sort_values("月間平均検索ボリューム", ascending=False)


def render() -> None:
    st.title("キーワード調査")
    settings = get_settings()
    if settings.ads_configured:
        st.success("Google Ads API モード（日本・日本語）")
    else:
        missing = "、".join(settings.missing_ads_settings)
        st.info(
            "ダミーモード: 設定画面で Google Ads API の認証情報を保存すると実データに切り替わります。"
            f" 未設定: {missing}"
        )

    uploaded = st.file_uploader("CSVからキーワードを読み込む（先頭列、UTF-8 / CP932）", type="csv")
    imported = []
    if uploaded:
        try:
            imported = keywords_from_csv(uploaded.getvalue())
            st.caption(f"{len(imported)} 件を読み込みました。")
        except ValueError as error:
            st.error(str(error))
    keyword_text = st.text_area("キーワード（1行に1件）", value="\n".join(imported), height=170, placeholder="創作 ブログ\n小説 書き方")
    force_refresh = st.checkbox("キャッシュを無視して再取得", value=settings.force_refresh)
    if st.button("検索指標を取得", type="primary"):
        keywords = normalize_keywords(keyword_text)
        if not keywords:
            st.warning("キーワードを1件以上入力してください。")
        else:
            try:
                with st.spinner(f"{len(keywords)} 件を調査中…"):
                    st.session_state.results = _service().research(keywords, force_refresh)
                st.success(f"{len(st.session_state.results)} 件の結果を取得しました。")
            except Exception as error:
                st.error(f"取得に失敗しました: {error}")

    st.divider()
    st.subheader("関連キーワード")
    source_type = st.radio("起点", ["キーワード", "URL"], horizontal=True)
    seed = st.text_input("起点キーワードまたはURL", placeholder="創作 ブログ または https://example.com/")
    if st.button("関連キーワードを取得"):
        if not seed.strip():
            st.warning("起点を入力してください。")
        else:
            try:
                with st.spinner("候補を取得中…"):
                    st.session_state.related_keywords = _service().related(seed.strip(), source_type == "URL", force_refresh)
            except Exception as error:
                st.error(f"取得に失敗しました: {error}")
    related = st.session_state.get("related_keywords", [])
    if related:
        chosen = st.multiselect("追加調査する関連キーワード", related, default=related)
        if st.button("選択した関連キーワードを調査"):
            try:
                with st.spinner("検索指標を取得中…"):
                    new_results = _service().research(chosen, force_refresh)
                existing = {item["keyword"].casefold(): item for item in st.session_state.get("results", [])}
                existing.update({item["keyword"].casefold(): item for item in new_results})
                st.session_state.results = list(existing.values())
                st.success(f"{len(new_results)} 件を追加しました。")
            except Exception as error:
                st.error(f"取得に失敗しました: {error}")

    results = st.session_state.get("results", [])
    if results:
        st.divider()
        st.subheader("検索結果")
        filtered = _filtered_results(results)
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button("CSVをエクスポート", to_excel_csv(filtered), "keyword_results.csv", "text/csv")
