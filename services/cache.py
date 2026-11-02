from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class JsonCache:
    """Small, fault-tolerant JSON cache; it never stores research history."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        try:
            content = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(content, dict):
                return {"metrics": content.get("metrics", {}), "related": content.get("related", {})}
        except (OSError, json.JSONDecodeError):
            pass
        return {"metrics": {}, "related": {}}

    def get(self, category: str, key: str, valid_days: int) -> Any | None:
        entry = self.data.get(category, {}).get(key)
        if not isinstance(entry, dict):
            return None
        try:
            saved_at = datetime.fromisoformat(entry["saved_at"])
            if datetime.now(UTC) - saved_at > timedelta(days=valid_days):
                return None
            return entry["value"]
        except (KeyError, TypeError, ValueError):
            return None

    def set(self, category: str, key: str, value: Any) -> None:
        self.data.setdefault(category, {})[key] = {
            "saved_at": datetime.now(UTC).isoformat(), "value": value
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def clear(self) -> None:
        self.data = {"metrics": {}, "related": {}}
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass
