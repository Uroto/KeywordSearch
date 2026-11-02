from __future__ import annotations

import hashlib
import re
from datetime import date
from typing import Protocol

from config import Settings


class KeywordProvider(Protocol):
    def fetch_metrics(self, keywords: list[str]) -> list[dict]: ...
    def suggest_keywords(self, seed: str, is_url: bool = False) -> list[str]: ...


class GoogleAdsAccessError(RuntimeError):
    """An API access-level error with an actionable message for the UI."""


def _month_name(month_number: int) -> str:
    return f"{month_number:02d}"


MONTH_NAME_TO_NUMBER = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
    "MAY": 5, "JUNE": 6, "JULY": 7, "AUGUST": 8,
    "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
}


class DummyKeywordProvider:
    """Deterministic sample provider for development without API credentials."""

    def _number(self, keyword: str) -> int:
        return int(hashlib.sha256(keyword.encode("utf-8")).hexdigest()[:8], 16)

    def fetch_metrics(self, keywords: list[str]) -> list[dict]:
        results = []
        today = date.today()
        for keyword in keywords:
            seed = self._number(keyword)
            average = ((seed % 190) + 1) * 100
            monthly = []
            for offset in range(11, -1, -1):
                year = today.year - ((today.month - offset - 1) // 12 < 0)
                month = (today.month - offset - 1) % 12 + 1
                volume = max(0, int(average * (0.68 + ((seed >> (offset % 16)) % 65) / 100)))
                monthly.append({"month": f"{year}-{_month_name(month)}", "volume": volume})
            competition = ["低", "中", "高"][seed % 3]
            results.append({
                "keyword": keyword, "average_monthly_searches": average,
                "competition": competition, "competition_index": seed % 101,
                "low_top_of_page_bid": round(20 + (seed % 180) / 10, 2),
                "high_top_of_page_bid": round(100 + (seed % 900) / 10, 2),
                "monthly_volumes": monthly, "source": "ダミー（開発用）",
            })
        return results

    def suggest_keywords(self, seed: str, is_url: bool = False) -> list[str]:
        base = seed.rstrip("/").split("/")[-1] if is_url else seed
        suffixes = ["とは", "おすすめ", "やり方", "初心者", "コツ", "比較", "無料", "ランキング"]
        return [f"{base} {suffix}" for suffix in suffixes]


class GoogleAdsKeywordProvider:
    def __init__(self, settings: Settings) -> None:
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError as error:
            raise RuntimeError("google-ads パッケージをインストールしてください。") from error
        config = {
            "client_id": settings.client_id, "client_secret": settings.client_secret,
            "refresh_token": settings.refresh_token,
            # Required by the Python client library when loading from a dict.
            "use_proto_plus": True,
        }
        if settings.login_customer_id:
            config["login_customer_id"] = settings.login_customer_id
        self.client = GoogleAdsClient.load_from_dict(config)
        self.settings = settings

    @staticmethod
    def _raise_translated_error(error: Exception) -> None:
        details = str(error)
        normalized = details.casefold()
        if (
            "developer_token_not_approved" in normalized
            and "explorer access" in normalized
        ):
            request_id_match = re.search(r"request_id:\s*[\"']?([^\s\"',}]+)", details)
            request_id = request_id_match.group(1) if request_id_match else None
            support_detail = f"（リクエスト ID: {request_id}）" if request_id else ""
            raise GoogleAdsAccessError(
                "Google Cloud プロジェクトの API アクセスが Explorer のため、"
                "検索指標・キーワード候補の取得は実行できません。"
                "Google Cloud Console の Google Ads API Overview でブランド確認を完了し、"
                "Basic アクセス以上へアップグレードしてください。"
                f"{support_detail}"
            ) from error
        raise error

    def fetch_metrics(self, keywords: list[str]) -> list[dict]:
        service = self.client.get_service("KeywordPlanIdeaService")
        request = self.client.get_type("GenerateKeywordHistoricalMetricsRequest")
        request.customer_id = self.settings.customer_id
        request.keywords.extend(keywords)
        request.geo_target_constants.append(f"geoTargetConstants/{self.settings.location_id}")
        request.language = f"languageConstants/{self.settings.language_id}"
        request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
        try:
            response = service.generate_keyword_historical_metrics(request=request)
        except Exception as error:
            self._raise_translated_error(error)
        results = []
        for item in response.results:
            metrics = item.keyword_metrics
            monthly = [
                {"month": f"{entry.year}-{self._month_number(entry.month):02d}", "volume": entry.monthly_searches}
                for entry in metrics.monthly_search_volumes
            ]
            results.append({
                "keyword": item.text, "average_monthly_searches": metrics.avg_monthly_searches,
                "competition": self._competition(metrics.competition),
                "competition_index": metrics.competition_index,
                "low_top_of_page_bid": self._micros_to_yen(metrics.low_top_of_page_bid_micros),
                "high_top_of_page_bid": self._micros_to_yen(metrics.high_top_of_page_bid_micros),
                "monthly_volumes": monthly, "source": "Google Ads API",
            })
        return results

    def suggest_keywords(self, seed: str, is_url: bool = False) -> list[str]:
        service = self.client.get_service("KeywordPlanIdeaService")
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = self.settings.customer_id
        request.language = f"languageConstants/{self.settings.language_id}"
        request.geo_target_constants.append(f"geoTargetConstants/{self.settings.location_id}")
        request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
        if is_url:
            request.url_seed.url = seed
        else:
            request.keyword_seed.keywords.append(seed)
        try:
            response = service.generate_keyword_ideas(request=request)
        except Exception as error:
            self._raise_translated_error(error)
        return list(dict.fromkeys(item.text for item in response))

    @staticmethod
    def _month_number(month: object) -> int:
        name = getattr(month, "name", str(month)).upper().rsplit(".", maxsplit=1)[-1]
        if name in MONTH_NAME_TO_NUMBER:
            return MONTH_NAME_TO_NUMBER[name]
        # Fallback for protobuf enum values: January=2 through December=13.
        numeric_value = int(month)
        if 2 <= numeric_value <= 13:
            return numeric_value - 1
        raise ValueError(f"Google Ads API returned an invalid month value: {month}")

    @staticmethod
    def _competition(value: object) -> str:
        name = getattr(value, "name", str(value)).upper()
        return {"LOW": "低", "MEDIUM": "中", "HIGH": "高"}.get(name, "不明")

    @staticmethod
    def _micros_to_yen(value: int) -> float | None:
        return round(value / 1_000_000, 2) if value else None


def create_provider(settings: Settings) -> KeywordProvider:
    return GoogleAdsKeywordProvider(settings) if settings.ads_configured else DummyKeywordProvider()
