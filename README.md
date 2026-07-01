# A 股 ETF 动量策略回测

这个项目用于回测一个简单的 A 股板块 ETF 趋势跟踪策略，并为后续扩展成完整量化系统打基础。

## 技术栈

- Python 3.10+
- 包管理：uv
- 数据源：AkShare 腾讯前复权接口，保留 EastMoney / 新浪演示配置
- 回测引擎：backtrader
- 本地缓存：parquet
- 可视化：matplotlib，内置中文字体候选配置

## 项目结构

```text
momentum-trader/
├── configs/default.yaml          # 策略、回测、数据和报告参数
├── data/raw/                     # AkShare 原始 parquet 缓存
├── data/processed/               # 预留的清洗后数据目录
├── outputs/                      # 图表、报表、交易明细输出
├── src/momentum_trader/
│   ├── cli.py                    # 命令行入口
│   ├── config.py                 # 配置模型与加载
│   ├── data/                     # 数据拉取、缓存、清洗
│   ├── strategy/                 # 信号与持仓规则
│   ├── backtest/                 # backtrader 引擎适配
│   ├── report/                   # 指标、绘图、导出
│   └── utils/                    # 日历、日志等工具
└── tests/                        # 单元测试
```

## 安装

```bash
uv sync
```

正式复现实验时建议使用锁文件：

```bash
uv sync --locked --dev
```

## 运行

一键拉数据、回测并导出报告：

```bash
uv run momentum-trader run --config configs/default.yaml
```

为一次实验指定标签，产物会归档到 `outputs/runs/{tag}/`，同时刷新 `outputs/report.html`：

```bash
uv run momentum-trader run --config configs/default.yaml --tag hs300-demo
```

默认配置使用腾讯前复权接口。如果需要验证备用展示流程，也可以用新浪日线演示配置：

```bash
uv run momentum-trader run --config configs/sina_demo.yaml
```

注意：`configs/sina_demo.yaml` 使用新浪 ETF 日线接口，不提供前复权参数，只适合验证工程流程和查看输出形态，不能替代正式前复权回测结论。

分步运行：

```bash
uv run momentum-trader fetch-data --config configs/default.yaml
uv run momentum-trader run-backtest --config configs/default.yaml
uv run momentum-trader report --config configs/default.yaml
```

## 测试

```bash
uv run pytest
```

## 输出产物

默认输出目录为 `outputs/`，新浪演示配置输出到 `outputs/sina_demo/`：

- `report.html`：最新一次回测的 HTML 报告，适合 localhost 固定预览
- `runs/{tag}/`：带标签的历史实验归档目录
- `index.csv`：每次导出报告追加一行实验索引，记录 tag、配置 SHA1、标的和核心指标
- `charts/equity_vs_hs300.png`：策略累计净值 vs 沪深 300 基准图
- `reports/equity_curve.csv`：每日账户权益曲线
- `reports/metrics.csv`：年化收益、夏普、最大回撤、卡玛、胜率等指标
- `reports/symbol_pnl.csv`：按 ETF 汇总的已闭合交易盈亏
- `trades/orders.csv`：逐笔订单成交明细
- `trades/closed_trades.csv`：已闭合交易明细

本地查看 HTML 报告：

```bash
uv run momentum-trader serve-report --config configs/default.yaml --port 8765
```

查看某个归档实验：

```bash
uv run momentum-trader serve-report --config configs/default.yaml --tag hs300-demo --port 8765
```

## 当前默认策略规则

- 默认标的：沪深 300 ETF（510300）
- 入场：收盘价突破过去 20 个交易日最高价，且 10 日均线大于 30 日均线
- 金字塔加仓：首仓 60%，上涨 3% 加 25%，上涨 6% 加 15%
- 止损：加仓阶段跌破 20 日均线清仓；加仓完成后，从持仓期间最高价回撤 8% 清仓
- 仓位：单 ETF 意向仓位为总资金 90%，默认只跟踪 510300，所以最多同时持有 1 只 ETF
- 交易：T 日收盘后生成信号，T+1 日开盘成交
- 成本：单边 0.15%

## 配置化策略

主要改 `configs/default.yaml` 即可快速实验：

- `universe`：调整跟踪的 ETF 代码和名称。
- `backtest`：调整回测起止日期、初始资金和现金利率。
- `execution`：调整单边成本和一字涨停判定阈值。
- `position`：调整最大持仓数、单 ETF 意向仓位和金字塔加仓阶梯；`pyramid.enabled: false` 时首仓直接打满意向仓位。
- `strategy.entry.conditions`：调整入场条件，`mode: all` 表示全部满足，`mode: any` 表示任一满足。
- `strategy.exit.conditions`：调整出场条件，`apply` 可设为 `before_pyramid_complete`、`after_pyramid_complete` 或 `always`。

当前支持的条件类型：

- `breakout`：价格突破过去 N 日某个价格字段的滚动高点，通常配 `shift: 1` 避免未来函数。
- `ma_relation`：快均线与慢均线比较，例如 60 日均线大于 250 日均线。
- `price_vs_ma` / `ma_break`：价格与某条均线比较，可用于入场过滤或跌破均线出场。
- `roc`：N 日涨跌幅与阈值比较。
- `rolling_mean_threshold`：某字段 N 日均值与阈值比较。
- `trailing_stop`：持仓高点回撤止损，这是持仓状态相关条件，只在回测执行层动态判断。

## 回测风险点处理

- 未来函数：信号生成在 `strategy/signals.py` 中统一处理，突破高点使用 `shift(1)`，只引用 T 日以前的高点；均线只使用 T 日及以前收盘价。
- 复权处理：默认使用 AkShare 腾讯日线接口并传入 `adjust: qfq`，所有信号和成交使用前复权价格。
- 涨跌停：`open_limit_up` 在执行日根据 T+1 开盘价和前收盘价标记；若 T+1 一字涨停，买入和加仓跳过。
- 停牌处理：不补齐缺失交易日，停牌日不会生成或执行交易。
- ETF 上市日期：数据从 AkShare 返回的首个有效交易日开始，早于上市日的回测起点自动失效。
