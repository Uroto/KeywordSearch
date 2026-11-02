from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class JsonCache:
    """Small, fault-tolerant JSON cache for keyword research results."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = self._load()
        if self._migrate_legacy_metric_months():
            self.save()

    def _load(self) -> dict[str, Any]:
        try:
            content = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(content, dict):
                return {
                    "schema_version": content.get("schema_version", 1),
                    "metrics": content.get("metrics", {}),
                    "related": content.get("related", {}),
                }
        except (OSError, json.JSONDecodeError):
            pass
        return {"schema_version": 2, "metrics": {}, "related": {}}

    def _migrate_legacy_metric_months(self) -> bool:
        """Fix month values written before MonthOfYear enum handling was corrected."""
        if self.data.get("schema_version", 1) >= 2:
            return False
        changed = False
        for entry in self.data.get("metrics", {}).values():
            value = entry.get("value") if isinstance(entry, dict) else None
            monthly_volumes = value.get("monthly_volumes") if isinstance(value, dict) else None
            if not isinstance(monthly_volumes, list):
                continue
            for monthly in monthly_volumes:
                month_text = monthly.get("month") if isinstance(monthly, dict) else None
                if not isinstance(month_text, str):
                    continue
                try:
                    year_text, month_number_text = month_text.split("-", maxsplit=1)
                    month_number = int(month_number_text)
                except ValueError:
                    continue
                # Older code wrote the protobuf enum value (January=2 … December=13).
                if 2 <= month_number <= 13:
                    monthly["month"] = f"{year_text}-{month_number - 1:02d}"
                    changed = True
        self.data["schema_version"] = 2
        return True

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

    def values(self, category: str, valid_days: int) -> list[Any]:
        """Return unexpired cached values in their original save order."""
        values = []
        for key in self.data.get(category, {}):
            value = self.get(category, key, valid_days)
            if value is not None:
                values.append(value)
        return values

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def clear(self) -> None:
        self.data = {"schema_version": 2, "metrics": {}, "related": {}}
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass
