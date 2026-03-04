# Tushare API 学习笔记

## 核心接口

### 1. pro_bar - 通用行情接口（推荐）
统一处理股票、ETF、指数等所有资产类型。

```python
import tushare as ts

ts.set_token('your_token')
pro = ts.pro_api()

# 股票日线
df = ts.pro_bar(
    ts_code='000977.SZ',
    asset='E',        # E=股票, FD=基金, I=指数
    adj='qfq',        # qfq前复权, hfq后复权, None不复权
    freq='D',         # D日线, W周线, M月线, 1/5/15/30/60分钟
    start_date='20250201',
    end_date='20250224'
)
```

**asset 参数：**
- `E` - A股股票
- `FD` - 基金（包括ETF）
- `I` - 沪深指数
- `FT` - 期货
- `C` - 数字货币
- `O` - 期权

### 2. daily - 股票日线（专用）
```python
df = pro.daily(ts_code='000977.SZ', start_date='20250201')
```
输出字段：ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount

### 3. fund_daily - 基金日线（已废弃，用pro_bar替代）
~~df = pro.fund_daily(ts_code='512480.SH')~~

### 4. stock_basic - 股票基础信息
```python
df = pro.stock_basic(
    ts_code='000977.SZ',
    fields='ts_code,name,industry,market,list_date'
)
```

### 5. fund_basic - 基金基础信息
```python
df = pro.fund_basic(
    ts_code='512480.SH',
    fields='ts_code,name,fund_type'
)
```

## 代码格式规范

| 格式 | 标准化结果 | 说明 |
|------|-----------|------|
| 000977 | 000977.SZ | 深圳主板（0/3开头） |
| 600519 | 600519.SH | 上海主板（6开头） |
| 688981 | 688981.SH | 科创板（68开头） |
| 300750 | 300750.SZ | 创业板（30开头） |
| 512480 | 512480.SH | ETF（5开头，上海） |
| 159915 | 159915.SZ | ETF（1开头，深圳） |

**判断规则：**
- 6xxxxx, 5xxxxx, 9xxxxx → .SH
- 0xxxxx, 3xxxxx, 2xxxxx, 1xxxxx → .SZ

## 积分与频率限制

- **基础积分（120分）**: 每分钟500次，每次6000条
- **5000积分**: 更高频次
- **数据更新时间**: 交易日15:00-16:00

## 最佳实践

1. **统一用 pro_bar**: 避免区分 daily/fund_daily
2. **加 timeout**: 网络请求可能超时
3. **处理复权**: 长期分析用前复权（qfq）
4. **批量查询**: 支持逗号分隔多代码，如 '000977.SZ,600519.SH'

## 量化交易常用接口

| 需求 | 接口 | 积分要求 |
|------|------|---------|
| 日线行情 | pro_bar/daily | 基础120 |
| 复权因子 | adj_factor | 2000+ |
| 分钟线 | pro_bar(freq='1MIN') | 5000+ |
| 资金流向 | moneyflow | 2000+ |
| 龙虎榜 | top_list | 5000+ |
| 财务报表 | income/balance/cashflow | 2000+ |
| 业绩预告 | forecast | 5000+ |

## 踩坑记录

1. **ETF不能用daily接口** → 用pro_bar(asset='FD') 或 fund_daily
2. **可转债** → cb_basic, cb_daily 专用接口
3. **涨停跌停** → limit_list 接口
4. **新股申购** → new_share 接口

---
Source: https://tushare.pro/document/2
Last Updated: 2026-02-24
