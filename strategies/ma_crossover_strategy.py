#!/usr/bin/env python3
"""
双均线策略实现
金叉买入，死叉卖出
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_stock_data(stock_code: str, start_date: str = None, end_date: str = None, period: str = "daily"):
    """
    获取股票历史数据
    
    Args:
        stock_code: 股票代码，如 "000001"
        start_date: 开始日期，如 "20230101"
        end_date: 结束日期
        period: daily/weekly/monthly
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 使用 AkShare 获取数据
    df = ak.stock_zh_a_hist(symbol=stock_code, period=period, 
                            start_date=start_date, end_date=end_date, adjust="qfq")
    
    # 重命名列
    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                  'amplitude', 'pct_change', 'change', 'turnover']
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    return df

def calculate_ma(df, short_window=5, long_window=20):
    """
    计算移动平均线
    
    Args:
        df: DataFrame with 'close' column
        short_window: 短期均线周期
        long_window: 长期均线周期
    """
    df[f'MA{short_window}'] = df['close'].rolling(window=short_window).mean()
    df[f'MA{long_window}'] = df['close'].rolling(window=long_window).mean()
    
    # 计算金叉死叉信号
    df['signal'] = 0
    df['position'] = 0
    
    # 金叉: 短期均线上穿长期均线
    # 死叉: 短期均线下穿长期均线
    for i in range(1, len(df)):
        if df[f'MA{short_window}'].iloc[i] > df[f'MA{long_window}'].iloc[i] and \
           df[f'MA{short_window}'].iloc[i-1] <= df[f'MA{long_window}'].iloc[i-1]:
            df.loc[i, 'signal'] = 1  # 金叉，买入
        elif df[f'MA{short_window}'].iloc[i] < df[f'MA{long_window}'].iloc[i] and \
             df[f'MA{short_window}'].iloc[i-1] >= df[f'MA{long_window}'].iloc[i-1]:
            df.loc[i, 'signal'] = -1  # 死叉，卖出
    
    return df

def backtest_strategy(df, initial_cash=100000, commission_rate=0.0003):
    """
    回测双均线策略
    
    Args:
        df: DataFrame with signals
        initial_cash: 初始资金
        commission_rate: 手续费率
    """
    cash = initial_cash
    position = 0
    trades = []
    
    for i in range(len(df)):
        price = df['close'].iloc[i]
        date = df['date'].iloc[i]
        signal = df['signal'].iloc[i]
        
        if signal == 1 and cash > 0:  # 金叉买入
            # 计算可买入股数（整手）
            max_shares = int(cash / price / 100) * 100
            if max_shares >= 100:
                cost = max_shares * price * (1 + commission_rate)
                if cost <= cash:
                    position = max_shares
                    cash -= cost
                    trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': price,
                        'shares': position,
                        'cost': cost
                    })
                    print(f"📈 {date.strftime('%Y-%m-%d')} 买入 {position}股 @ {price:.2f}")
        
        elif signal == -1 and position > 0:  # 死叉卖出
            revenue = position * price * (1 - commission_rate)
            trades.append({
                'date': date,
                'action': 'SELL',
                'price': price,
                'shares': position,
                'revenue': revenue
            })
            print(f"📉 {date.strftime('%Y-%m-%d')} 卖出 {position}股 @ {price:.2f}")
            cash += revenue
            position = 0
    
    # 计算最终市值
    final_price = df['close'].iloc[-1]
    final_value = cash + position * final_price
    
    # 计算收益
    total_return = (final_value - initial_cash) / initial_cash * 100
    
    # 计算 Buy and Hold 收益
    first_price = df['close'].iloc[0]
    bh_return = (final_price - first_price) / first_price * 100
    
    # 计算策略胜率
    if len(trades) >= 2:
        profits = []
        for i in range(0, len(trades)-1, 2):
            if trades[i]['action'] == 'BUY' and trades[i+1]['action'] == 'SELL':
                profit = trades[i+1]['revenue'] - trades[i]['cost']
                profits.append(profit)
        win_rate = len([p for p in profits if p > 0]) / len(profits) * 100 if profits else 0
    else:
        win_rate = 0
    
    return {
        'initial_cash': initial_cash,
        'final_value': final_value,
        'total_return': total_return,
        'buy_hold_return': bh_return,
        'outperform': total_return - bh_return,
        'trades_count': len(trades),
        'win_rate': win_rate,
        'trades': trades
    }

def plot_signals(df, stock_name=""):
    """打印买卖信号点"""
    print(f"\n{'='*60}")
    print(f"📊 {stock_name} 双均线策略信号")
    print(f"{'='*60}")
    
    buy_signals = df[df['signal'] == 1]
    sell_signals = df[df['signal'] == -1]
    
    print(f"\n金叉买入信号 ({len(buy_signals)}次):")
    for _, row in buy_signals.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')} @ {row['close']:.2f} "
              f"(MA5={row['MA5']:.2f}, MA20={row['MA20']:.2f})")
    
    print(f"\n死叉卖出信号 ({len(sell_signals)}次):")
    for _, row in sell_signals.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')} @ {row['close']:.2f} "
              f"(MA5={row['MA5']:.2f}, MA20={row['MA20']:.2f})")

def main():
    """主函数"""
    # 配置
    stock_code = "600362"  # 江西铜业
    stock_name = "江西铜业"
    start_date = "20240101"
    short_window = 5
    long_window = 20
    
    print(f"🚀 双均线策略回测")
    print(f"股票: {stock_name} ({stock_code})")
    print(f"均线: MA{short_window} / MA{long_window}")
    print(f"{'='*60}\n")
    
    # 1. 获取数据
    print("📥 获取股票数据...")
    df = get_stock_data(stock_code, start_date)
    print(f"✅ 获取 {len(df)} 条数据\n")
    
    # 2. 计算均线
    print("📊 计算技术指标...")
    df = calculate_ma(df, short_window, long_window)
    print("✅ 计算完成\n")
    
    # 3. 打印信号
    plot_signals(df, stock_name)
    
    # 4. 回测
    print(f"\n{'='*60}")
    print("💰 回测结果")
    print(f"{'='*60}")
    
    result = backtest_strategy(df)
    
    print(f"\n初始资金: ¥{result['initial_cash']:,.0f}")
    print(f"最终市值: ¥{result['final_value']:,.0f}")
    print(f"策略收益: {result['total_return']:+.2f}%")
    print(f"持有收益: {result['buy_hold_return']:+.2f}%")
    print(f"超额收益: {result['outperform']:+.2f}%")
    print(f"交易次数: {result['trades_count']}次")
    print(f"胜率: {result['win_rate']:.1f}%")
    
    if result['outperform'] > 0:
        print(f"\n✅ 策略跑赢持有 {result['outperform']:.2f}%")
    else:
        print(f"\n⚠️ 策略跑输持有 {abs(result['outperform']):.2f}%")
    
    return result

if __name__ == "__main__":
    main()
