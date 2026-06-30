# A 股 ETF 动量策略回测

这个项目用于回测一个简单的 A 股板块 ETF 趋势跟踪策略，并为后续扩展成完整量化系统打基础。

## 技术栈

- Python 3.10+
- 包管理：uv
- 数据源：AkShare
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

## 运行

一键拉数据、回测并导出报告：

```bash
uv run momentum-trader run --config configs/default.yaml
```

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

## 当前策略规则

- 标的池：沪深 300 ETF、中证 500 ETF、半导体 ETF、创新药 ETF、光伏 ETF、恒生科技 ETF
- 入场：收盘价突破过去 120 个交易日最高价，且 60 日均线大于 250 日均线
- 金字塔加仓：首仓 50%，上涨 10% 加 30%，上涨 20% 加 20%
- 止损：加仓阶段跌破 60 日均线清仓；加仓完成后，从持仓期间最高价回撤 15% 清仓
- 仓位：单 ETF 意向仓位为总资金 30%，最多同时持有 2 只 ETF
- 交易：T 日收盘后生成信号，T+1 日开盘成交
- 成本：单边 0.15%

## 回测风险点处理

- 未来函数：信号生成在 `strategy/signals.py` 中统一处理，突破高点使用 `shift(1)`，只引用 T 日以前的高点；均线只使用 T 日及以前收盘价。
- 复权处理：AkShare ETF 日线拉取使用 `adjust: qfq`，所有信号和成交使用前复权价格。
- 涨跌停：`open_limit_up` 在执行日根据 T+1 开盘价和前收盘价标记；若 T+1 一字涨停，买入和加仓跳过。
- 停牌处理：不补齐缺失交易日，停牌日不会生成或执行交易。
- ETF 上市日期：数据从 AkShare 返回的首个有效交易日开始，早于上市日的回测起点自动失效。

