from __future__ import annotations

import streamlit as st

from config import CACHE_FILE, get_settings, save_settings
from services.cache import JsonCache


def render() -> None:
    st.title("設定")
    settings = get_settings()
    st.caption("認証情報はローカルの `.env` に保存され、Gitの管理対象外です。")
    with st.form("settings"):
        st.subheader("Google Ads API 認証")
        client_id = st.text_input("OAuth クライアントID", value=settings.client_id, type="password")
        client_secret = st.text_input("OAuth クライアントシークレット", value=settings.client_secret, type="password")
        refresh_token = st.text_input("リフレッシュトークン", value=settings.refresh_token, type="password")
        customer_id = st.text_input("Google Ads お客様ID（ハイフンなし）", value=settings.customer_id)
        login_customer_id = st.text_input("ログインお客様ID（任意、MCC用）", value=settings.login_customer_id)
        st.subheader("対象・キャッシュ")
        location_id = st.text_input("地域ID（日本: 2392）", value=settings.location_id)
        language_id = st.text_input("言語ID（日本語: 1005）", value=settings.language_id)
        related_days = st.number_input("関連キーワードのキャッシュ日数", min_value=0, value=settings.related_cache_days)
        metrics_days = st.number_input("検索指標のキャッシュ日数", min_value=0, value=settings.metrics_cache_days)
        batch_size = st.number_input("API一括取得数", min_value=1, max_value=10000, value=settings.batch_size)
        force_refresh = st.checkbox("常にキャッシュを無視する", value=settings.force_refresh)
        submitted = st.form_submit_button("設定を保存")
    if submitted:
        save_settings({"client_id": client_id, "client_secret": client_secret,
                       "refresh_token": refresh_token, "customer_id": customer_id, "login_customer_id": login_customer_id,
                       "location_id": location_id, "language_id": language_id, "related_cache_days": related_days,
                       "metrics_cache_days": metrics_days, "batch_size": batch_size, "force_refresh": force_refresh})
        st.success("設定を保存しました。")
    st.divider()
    st.subheader("キャッシュ")
    if st.button("キャッシュを全削除", type="secondary"):
        JsonCache(CACHE_FILE).clear()
        st.success("キャッシュを削除しました。")
