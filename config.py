from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
CACHE_FILE = DATA_DIR / "keyword_cache.json"


def _integer(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _boolean(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    client_id: str = ""
    client_secret: str = ""
    refresh_token: str = ""
    customer_id: str = ""
    login_customer_id: str = ""
    location_id: str = "2392"  # Japan
    language_id: str = "1005"  # Japanese
    related_cache_days: int = 7
    metrics_cache_days: int = 30
    force_refresh: bool = False
    batch_size: int = 1000

    @property
    def ads_configured(self) -> bool:
        return not self.missing_ads_settings

    @property
    def missing_ads_settings(self) -> tuple[str, ...]:
        required = {
            "OAuth クライアント ID": self.client_id,
            "OAuth クライアント シークレット": self.client_secret,
            "リフレッシュ トークン": self.refresh_token,
            "Google Ads お客様 ID": self.customer_id,
        }
        return tuple(label for label, value in required.items() if not value)


def get_settings() -> Settings:
    load_dotenv(ENV_FILE, override=True)
    return Settings(
        client_id=os.getenv("GOOGLE_ADS_CLIENT_ID", "").strip(),
        client_secret=os.getenv("GOOGLE_ADS_CLIENT_SECRET", "").strip(),
        refresh_token=os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "").strip(),
        customer_id=os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "").strip(),
        login_customer_id=os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "").strip(),
        location_id=os.getenv("TARGET_LOCATION_ID", "2392").strip(),
        language_id=os.getenv("TARGET_LANGUAGE_ID", "1005").strip(),
        related_cache_days=max(0, _integer("CACHE_RELATED_DAYS", 7)),
        metrics_cache_days=max(0, _integer("CACHE_METRICS_DAYS", 30)),
        force_refresh=_boolean("CACHE_FORCE_REFRESH"),
        batch_size=max(1, _integer("BATCH_SIZE", 1000)),
    )


def save_settings(values: dict[str, str | int | bool]) -> None:
    ENV_FILE.touch(exist_ok=True)
    mapping = {
        "client_id": "GOOGLE_ADS_CLIENT_ID",
        "client_secret": "GOOGLE_ADS_CLIENT_SECRET", "refresh_token": "GOOGLE_ADS_REFRESH_TOKEN",
        "customer_id": "GOOGLE_ADS_CUSTOMER_ID", "login_customer_id": "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "location_id": "TARGET_LOCATION_ID", "language_id": "TARGET_LANGUAGE_ID",
        "related_cache_days": "CACHE_RELATED_DAYS", "metrics_cache_days": "CACHE_METRICS_DAYS",
        "force_refresh": "CACHE_FORCE_REFRESH", "batch_size": "BATCH_SIZE",
    }
    for field, env_name in mapping.items():
        if field in values:
            set_key(str(ENV_FILE), env_name, str(values[field]))
