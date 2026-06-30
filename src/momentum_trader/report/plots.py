from __future__ import annotations

from pathlib import Path

import pandas as pd


def configure_chinese_fonts(font_candidates: list[str]) -> None:
    import matplotlib.pyplot as plt

    if font_candidates:
        plt.rcParams["font.sans-serif"] = font_candidates
    plt.rcParams["axes.unicode_minus"] = False


def plot_equity_vs_benchmark(
    equity_curve: pd.DataFrame,
    benchmark: pd.DataFrame,
    output_path: Path,
    font_candidates: list[str],
) -> None:
    import matplotlib.pyplot as plt

    configure_chinese_fonts(font_candidates)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    if not equity_curve.empty:
        strategy_nav = equity_curve["equity"] / equity_curve["equity"].iloc[0]
        ax.plot(equity_curve["date"], strategy_nav, label="策略累计净值", linewidth=2)

    if not benchmark.empty:
        benchmark_nav = benchmark["close"] / benchmark["close"].iloc[0]
        ax.plot(benchmark["date"], benchmark_nav, label="沪深300基准", linewidth=1.5)

    ax.set_title("累计净值曲线")
    ax.set_xlabel("日期")
    ax.set_ylabel("累计净值")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)

