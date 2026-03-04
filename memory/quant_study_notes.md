# A股量化策略学习笔记

> 学习目标：系统学习 A 股量化交易策略，结合实际数据（AkShare/adata）实现可运行的策略

---

## 📚 学习资源清单

### 1. 量化平台（待深入研究）
| 平台 | 特点 | 网址 |
|------|------|------|
| **聚宽 (JoinQuant)** | 最主流，社区活跃，回测完善 | joinquant.com |
| **米筐 (RiceQuant)** | 数据质量好，机构用户多 | ricequant.com |
| **优矿 (Uqer)** | 通联数据旗下，数据全面 | uqer.io |
| **掘金量化** | 本地化部署，适合实盘 | myquant.cn |

### 2. 论坛社区
- **雪球** - 投资者交流，策略分享
- **集思录** - 低风险套利策略较多
- **知乎专栏** - 量化理论文章
- **GitHub** - 开源策略代码

### 3. Python 库
- `jqfactor` - 聚宽因子库
- `alphalens` - 因子分析
- `pyfolio` - 绩效分析
- `backtrader` - 回测框架

---

## 🎯 A股量化策略分类

### 一、技术分析类（Trend Following）

#### 1. 均线策略
```python
# 核心逻辑
金叉买入: MA5 上穿 MA20
死叉卖出: MA5 下穿 MA20

变体：
- 双均线 → 三均线（MA5/MA10/MA30）
- 均线多头排列/空头排列
- 均线偏离度（股价与均线距离）
```

#### 2. MACD 策略
```python
# 核心逻辑
DIF 上穿 DEA (金叉) → 买入
DIF 下穿 DEA (死叉) → 卖出

A股特点：
- MACD 顶背离（股价新高，MACD 未新高）→ 卖出信号
- MACD 底背离（股价新低，MACD 未新低）→ 买入信号
```

#### 3. RSI 超买超卖
```python
RSI > 70 → 超买，考虑卖出
RSI < 30 → 超卖，考虑买入

A股优化：
- 牛市 RSI 80 才超买
- 熊市 RSI 20 才超卖
- 结合成交量确认
```

#### 4. 布林带 (Bollinger Bands)
```python
# 核心逻辑
股价触及下轨 → 买入
股价触及上轨 → 卖出

变体：
- 布林带收窄 → 突破前兆（波动率收缩）
- 布林带开口 → 趋势确立
```

#### 5. KDJ 随机指标
```python
# A股短线常用
K 上穿 D 金叉 → 买入
K 下穿 D 死叉 → 卖出
J > 100 超买, J < 0 超卖
```

---

### 二、资金流向类

#### 1. 主力资金跟踪
```python
# 我们已实现的监控
- 超大单净流入（机构动向）
- 大单净流入（大户动向）
- 主力净流入 = 超大单 + 大单

策略逻辑：
- 尾盘主力大幅流入 → 次日高开概率大
- 连续3日主力流入 → 启动信号
- 股价上涨但主力流出 → 诱多/出货
```

#### 2. 板块轮动
```python
# 资金流向板块排名
- 获取行业板块资金流入排名
- 获取概念板块资金流入排名

策略逻辑：
- 资金流向板块 TOP5 → 热点板块
- 连续多日流入同一板块 → 主线确立
- 与技术指标结合（放量突破）
```

#### 3. 北向资金（陆股通）
```python
# 外资动向
- 北向资金连续3日流入 → 看涨信号
- 单日流入超100亿 → 强烈看多
- 与市场走势背离 → 留意拐点
```

---

### 三、多因子选股类

#### 1. 价值因子
```python
- PE（市盈率）< 行业平均
- PB（市净率）< 1
- ROE > 15%
- 股息率 > 3%
```

#### 2. 成长因子
```python
- 营收增长率 > 20%
- 净利润增长率 > 20%
- 连续3年增长
```

#### 3. 质量因子
```python
- ROE 稳定性（标准差小）
- 资产负债率低
- 现金流健康
```

#### 4. 动量因子
```python
- 过去20日涨幅排名前10%
- 量价齐升
- 突破近期新高
```

#### 5. 反转因子
```python
# A股特色：涨跌停板制度导致动量/反转并存
- 过去5日跌幅前10% → 超跌反弹
- 结合 RSI < 30
- 避开连续跌停的股票
```

---

### 四、事件驱动类

#### 1. 财报季策略
```python
- 业绩预增 → 提前布局
- 超预期财报 → 次日高开
- 分红送转 → 填权行情
```

#### 2. 龙虎榜策略
```python
- 知名游资席位买入 → 短期热点
- 机构专用席位买入 → 中线看好
- 区分真假机构（核查席位历史）
```

#### 3. 新股策略
```python
- 开板首日买入策略
- 次新股超跌反弹
```

---

### 五、套利类

#### 1. 期现套利
```python
- 股指期货升水/贴水套利
- 需要融券和期货账户
```

#### 2. ETF 套利
```python
- ETF 净值与价格偏离
- 一二级市场套利
```

#### 3. 可转债套利
```python
- 双低策略（低价格+低溢价率）
- 转股溢价率 < 10%
- 到期收益率 > 0%
```

---

## 🛠️ 策略实现框架

### 数据获取（我们已有的）
```python
# 1. 历史行情数据
import akshare as ak
df = ak.stock_zh_a_hist(symbol="000001", period="daily")

# 2. 实时资金流向
from adata import stock
df = stock.market.baidu_capital_flow.get_capital_flow_min(stock_code='000001')

# 3. 财务数据
df = ak.stock_financial_report_em(stock="600519", symbol="利润表")
```

### 技术指标计算
```python
import pandas as pd
import numpy as np

# MA 均线
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA20'] = df['close'].rolling(window=20).mean()

# RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# MACD
exp1 = df['close'].ewm(span=12, adjust=False).mean()
exp2 = df['close'].ewm(span=26, adjust=False).mean()
df['DIF'] = exp1 - exp2
df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
df['MACD'] = 2 * (df['DIF'] - df['DEA'])
```

### 回测框架（简化版）
```python
def backtest(df, strategy_func, initial_cash=100000):
    """
    简化回测框架
    
    Args:
        df: DataFrame with OHLCV data
        strategy_func: 返回买卖信号的函数
        initial_cash: 初始资金
    
    Returns:
        回测结果字典
    """
    cash = initial_cash
    position = 0  # 持仓股数
    trades = []
    
    for i in range(1, len(df)):
        signal = strategy_func(df.iloc[:i+1])
        price = df.iloc[i]['close']
        date = df.iloc[i]['date']
        
        if signal == 'BUY' and cash > 0:
            # 全仓买入
            position = int(cash / price / 100) * 100  # 整手
            cash -= position * price
            trades.append({'date': date, 'action': 'BUY', 'price': price, 'amount': position})
            
        elif signal == 'SELL' and position > 0:
            # 全仓卖出
            cash += position * price
            trades.append({'date': date, 'action': 'SELL', 'price': price, 'amount': position})
            position = 0
    
    # 最终市值
    final_value = cash + position * df.iloc[-1]['close']
    return {
        'initial_cash': initial_cash,
        'final_value': final_value,
        'return': (final_value - initial_cash) / initial_cash,
        'trades': trades
    }
```

---

## 📈 下一步学习计划

### 短期（1-2周）
1. ✅ 实现资金流向监控（已完成）
2. ⏳ 实现双均线策略并回测
3. ⏳ 实现 RSI 超买超卖策略
4. ⏳ 实现 MACD 金叉死叉策略

### 中期（1个月）
5. 多因子选股策略
6. 板块轮动策略
7. 龙虎榜监控

### 长期（3个月）
8. 策略组合与风险对冲
9. 机器学习选股
10. 实盘模拟与优化

---

## 📝 参考资料

- 《Python量化交易实战》- 王小川
- 《因子投资：方法与实践》- 石川等
- 《主动投资组合管理》- Grinold & Kahn
- 聚宽官方文档: https://www.joinquant.com/help/api/help

---

*记录时间: 2026-02-25*
*数据来源: AkShare / adata*
