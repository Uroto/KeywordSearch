from __future__ import annotations

from io import BytesIO

import pandas as pd


DISPLAY_COLUMNS = {
    "keyword": "キーワード", "average_monthly_searches": "月間平均検索ボリューム",
    "competition": "競合性", "competition_index": "競合指数",
    "low_top_of_page_bid": "入札単価（低・円）", "high_top_of_page_bid": "入札単価（高・円）",
    "source": "取得元",
}


def results_frame(results: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(results)
    if frame.empty:
        return pd.DataFrame(columns=DISPLAY_COLUMNS.values())
    return frame.drop(columns=["monthly_volumes"], errors="ignore").rename(columns=DISPLAY_COLUMNS)


def to_excel_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def keywords_from_csv(content: bytes) -> list[str]:
    for encoding in ("utf-8-sig", "cp932"):
        try:
            frame = pd.read_csv(BytesIO(content), encoding=encoding, header=None)
            return [str(value).strip() for value in frame.iloc[:, 0].dropna() if str(value).strip()]
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    raise ValueError("CSVを読み込めませんでした。UTF-8 または CP932 を使用してください。")
