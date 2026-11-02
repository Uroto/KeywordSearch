from __future__ import annotations

from config import Settings
from services.cache import JsonCache
from services.google_ads import KeywordProvider


def normalize_keywords(text: str) -> list[str]:
    seen: set[str] = set()
    keywords = []
    for line in text.splitlines():
        keyword = " ".join(line.strip().split())
        key = keyword.casefold()
        if keyword and key not in seen:
            seen.add(key)
            keywords.append(keyword)
    return keywords


class KeywordResearchService:
    def __init__(self, provider: KeywordProvider, cache: JsonCache, settings: Settings) -> None:
        self.provider, self.cache, self.settings = provider, cache, settings

    def research(self, keywords: list[str], force_refresh: bool = False) -> list[dict]:
        saved: dict[str, dict] = {}
        needed = []
        for keyword in keywords:
            cached = None if force_refresh else self.cache.get("metrics", keyword.casefold(), self.settings.metrics_cache_days)
            if cached:
                saved[keyword.casefold()] = cached
            else:
                needed.append(keyword)
        for start in range(0, len(needed), self.settings.batch_size):
            for record in self.provider.fetch_metrics(needed[start:start + self.settings.batch_size]):
                key = record["keyword"].casefold()
                self.cache.set("metrics", key, record)
                saved[key] = record
        self.cache.save()
        return [saved[keyword.casefold()] for keyword in keywords if keyword.casefold() in saved]

    def related(self, seed: str, is_url: bool = False, force_refresh: bool = False) -> list[str]:
        cache_key = f"{'url' if is_url else 'keyword'}:{seed.casefold()}"
        cached = None if force_refresh else self.cache.get("related", cache_key, self.settings.related_cache_days)
        if cached:
            return cached
        suggestions = self.provider.suggest_keywords(seed, is_url)
        unique = list(dict.fromkeys(keyword.strip() for keyword in suggestions if keyword.strip()))
        self.cache.set("related", cache_key, unique)
        self.cache.save()
        return unique
