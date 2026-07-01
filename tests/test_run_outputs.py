from __future__ import annotations

import pandas as pd

from momentum_trader.config import load_config
from momentum_trader.report.run_outputs import append_run_index, build_output_locations


def test_build_output_locations_sanitizes_tag_and_keeps_latest_at_root(tmp_path) -> None:
    locations = build_output_locations(tmp_path, "hs300 / demo")

    assert locations.tag == "hs300_demo"
    assert locations.run_dir == tmp_path / "runs" / "hs300_demo"
    assert locations.latest_dir == tmp_path
    assert locations.index_path == tmp_path / "index.csv"


def test_append_run_index_records_metrics_and_config_hash(tmp_path) -> None:
    cfg = load_config("configs/default.yaml")
    locations = build_output_locations(tmp_path, "demo")
    reports_dir = locations.run_dir / "reports"
    reports_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "equity": 1_234_567.0,
            }
        ]
    ).to_csv(reports_dir / "equity_curve.csv", index=False)
    pd.DataFrame(
        [
            {
                "annual_return": 0.12,
                "sharpe": 1.3,
                "max_drawdown": -0.08,
            }
        ]
    ).to_csv(reports_dir / "metrics.csv", index=False)

    index_path = append_run_index(cfg, locations)

    index = pd.read_csv(index_path)
    row = index.iloc[0]
    assert row["tag"] == "demo"
    assert str(row["universe"]) == "510300"
    assert row["final_equity"] == 1_234_567.0
    assert row["annual_return"] == 0.12
    assert row["config_sha1"]
