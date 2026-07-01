from __future__ import annotations

import json
from datetime import date

import pandas as pd

from momentum_trader.data.cache import ParquetCache


def test_cache_key_uses_end_date_for_completed_history(tmp_path) -> None:
    cache = ParquetCache(tmp_path, today_provider=lambda: date(2026, 6, 30))

    key = cache.key(
        "tencent_etf",
        "510300",
        "2015-01-01",
        "2024-12-31",
        "qfq",
        source="tencent",
    )

    assert key.fetch_date == "20241231"
    assert key.filename() == "510300_20150101_20241231_qfq_20241231.parquet"


def test_cache_key_uses_today_for_live_or_future_history(tmp_path) -> None:
    cache = ParquetCache(tmp_path, today_provider=lambda: date(2026, 6, 30))

    today_key = cache.key("tencent_etf", "510300", "2026-01-01", "2026-06-30", "qfq")
    future_key = cache.key("tencent_etf", "510300", "2026-01-01", "2026-12-31", "qfq")

    assert today_key.fetch_date == "20260630"
    assert future_key.fetch_date == "20260630"


def test_read_or_fetch_reuses_parquet_and_writes_metadata(tmp_path) -> None:
    cache = ParquetCache(tmp_path, today_provider=lambda: date(2026, 6, 30))
    key = cache.key(
        "tencent_etf",
        "510300",
        "2015-01-01",
        "2024-12-31",
        "qfq",
        source="tencent",
    )
    calls = 0

    def fetcher() -> pd.DataFrame:
        nonlocal calls
        calls += 1
        return pd.DataFrame({"date": pd.to_datetime(["2024-01-02"]), "close": [1.23]})

    first = cache.read_or_fetch(key, fetcher)
    second = cache.read_or_fetch(
        key,
        lambda: pd.DataFrame({"date": pd.to_datetime(["2024-01-03"]), "close": [9.99]}),
    )

    assert calls == 1
    pd.testing.assert_frame_equal(first, second)
    metadata = json.loads((tmp_path / "tencent_etf" / "_metadata.json").read_text())
    entry = metadata["files"][key.filename()]
    assert entry["source"] == "tencent"
    assert entry["symbol"] == "510300"
    assert entry["fetch_date"] == "20241231"
    assert entry["akshare_version"]
