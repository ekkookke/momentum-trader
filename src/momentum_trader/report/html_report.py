from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

from momentum_trader.config import AppConfig

METRIC_LABELS = {
    "annual_return": "年化收益",
    "sharpe": "夏普比率",
    "max_drawdown": "最大回撤",
    "calmar": "卡玛比率",
    "win_rate": "胜率",
    "profit_loss_ratio": "盈亏比",
    "avg_holding_bars": "平均持仓周期",
    "total_trades": "闭合交易数",
    "total_orders": "订单数",
    "total_fees": "手续费合计",
}

PERCENT_METRICS = {"annual_return", "max_drawdown", "win_rate"}
NUMBER_METRICS = {"sharpe", "calmar", "profit_loss_ratio"}


def export_html_report(
    config: AppConfig,
    metrics: pd.DataFrame,
    symbol_pnl: pd.DataFrame,
    orders: pd.DataFrame,
    closed_trades: pd.DataFrame,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metric_row = metrics.iloc[0].to_dict() if not metrics.empty else {}

    warning = ""
    if config.data.source == "sina":
        warning = (
            "<div class='notice'>当前报告使用新浪演示数据源。新浪 ETF 日线不提供前复权参数，"
            "该结果只用于验证工程管线和产物形态，不作为正式 qfq 回测结论。</div>"
        )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(config.project.name)} 回测报告</title>
  <style>
    :root {{
      --bg: #f7f5ef;
      --panel: #ffffff;
      --ink: #222426;
      --muted: #6d6a62;
      --line: #d8d1c4;
      --green: #15855e;
      --red: #b73b3b;
      --amber: #a06a12;
      --blue: #256d85;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      line-height: 1.5;
    }}
    header {{
      padding: 28px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: #fcfbf8;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 650;
      letter-spacing: 0;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    main {{ padding: 22px 32px 40px; }}
    section {{ margin: 0 0 24px; }}
    h2 {{
      margin: 0 0 12px;
      font-size: 18px;
      font-weight: 650;
    }}
    .notice {{
      margin: 18px 32px 0;
      padding: 12px 14px;
      border-left: 4px solid var(--amber);
      background: #fff7e4;
      color: #654205;
      font-size: 14px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }}
    .metric {{
      min-height: 78px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 13px;
    }}
    .metric-value {{
      margin-top: 6px;
      font-size: 22px;
      font-weight: 700;
      color: var(--ink);
    }}
    .positive {{ color: var(--green); }}
    .negative {{ color: var(--red); }}
    .chart {{
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      padding: 12px;
    }}
    .chart img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      white-space: nowrap;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid #ebe5d9;
      text-align: right;
    }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{
      color: var(--muted);
      font-weight: 650;
      background: #fbfaf6;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }}
    .links a {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--blue);
      background: var(--panel);
      text-decoration: none;
      font-size: 13px;
    }}
    @media (max-width: 720px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .notice {{ margin-left: 16px; margin-right: 16px; }}
      h1 {{ font-size: 22px; }}
      .metric-value {{ font-size: 19px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(config.project.name)} 回测报告</h1>
    <div class="meta">
      <span>区间：{escape(config.backtest.start_date)} 至 {escape(config.backtest.end_date)}</span>
      <span>数据源：{escape(config.data.source)}</span>
      <span>复权：{escape(config.data.adjust)}</span>
      <span>初始资金：{config.backtest.initial_cash:,.0f}</span>
    </div>
  </header>
  {warning}
  <main>
    <section>
      <h2>核心指标</h2>
      <div class="metrics">
        {_render_metric_cards(metric_row)}
      </div>
    </section>
    <section>
      <h2>累计净值</h2>
      <div class="chart">
        <img src="charts/equity_vs_hs300.png" alt="策略累计净值与沪深300基准对比">
      </div>
    </section>
    <section>
      <h2>ETF 贡献拆分</h2>
      {_render_table(symbol_pnl, max_rows=20)}
    </section>
    <section>
      <h2>闭合交易明细</h2>
      {_render_table(closed_trades, max_rows=50)}
    </section>
    <section>
      <h2>订单明细</h2>
      {_render_table(orders, max_rows=80)}
      <div class="links">
        <a href="reports/metrics.csv">metrics.csv</a>
        <a href="reports/symbol_pnl.csv">symbol_pnl.csv</a>
        <a href="reports/equity_curve.csv">equity_curve.csv</a>
        <a href="trades/orders.csv">orders.csv</a>
        <a href="trades/closed_trades.csv">closed_trades.csv</a>
      </div>
    </section>
  </main>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _render_metric_cards(metric_row: dict) -> str:
    cards = []
    for key, label in METRIC_LABELS.items():
        value = metric_row.get(key)
        formatted = _format_metric(key, value)
        direction_class = _value_class(key, value)
        cards.append(
            f"<div class='metric'><div class='metric-label'>{escape(label)}</div>"
            f"<div class='metric-value {direction_class}'>{escape(formatted)}</div></div>"
        )
    return "\n".join(cards)


def _format_metric(key: str, value) -> str:
    if pd.isna(value):
        return "-"
    if key in PERCENT_METRICS:
        return f"{float(value):.2%}"
    if key in NUMBER_METRICS:
        return f"{float(value):.3f}"
    if key == "avg_holding_bars":
        return f"{float(value):.1f} 天"
    if key == "total_fees":
        return f"{float(value):,.2f}"
    if key in {"total_trades", "total_orders"}:
        return f"{int(value):,}"
    return str(value)


def _value_class(key: str, value) -> str:
    if pd.isna(value):
        return ""
    if key in {"annual_return", "sharpe", "calmar", "pnl_after_cost"}:
        return "positive" if float(value) > 0 else "negative" if float(value) < 0 else ""
    if key == "max_drawdown":
        return "negative" if float(value) < 0 else ""
    return ""


def _render_table(df: pd.DataFrame, max_rows: int) -> str:
    if df.empty:
        return (
            "<div class='table-wrap'><table><tbody><tr><td>暂无数据</td></tr>"
            "</tbody></table></div>"
        )

    display = df.head(max_rows).copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].map(
                lambda value: "" if pd.isna(value) else f"{value:,.4f}"
            )
    header = "".join(f"<th>{escape(str(column))}</th>" for column in display.columns)
    rows = []
    for _, row in display.iterrows():
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row.tolist())
        rows.append(f"<tr>{cells}</tr>")
    return (
        "<div class='table-wrap'><table>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )
