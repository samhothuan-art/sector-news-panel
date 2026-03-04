#!/usr/bin/env python3
"""
RSI 超买超卖策略 + 资金流向策略
结合技术指标和主力资金流向
"""

import akshare as ak
import adata
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_stock_data(stock_code: str, days: int = 120):
    """获取股票历史数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days*2)  # 多取一些数据用于计算指标
    
    df = ak.stock_zh_a_hist(symbol=stock_code, period="daily",
                            start_date=start_date.strftime("%Y%m%d"),
                            end_date=end_date.strftime("%Y%m%d"),
                            adjust="qfq")
    
    df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount',
                  'amplitude', 'pct_change', 'change', 'turnover']
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # 只保留最近 days 天
    if len(df) > days:
        df = df.tail(days).reset_index(drop=True)
    
    return df

def calculate_rsi(df, period=14):
    """计算 RSI 指标"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df):
    """计算 MACD 指标"""
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp1 - exp2
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    return df

def get_capital_flow_signal(stock_code: str):
    """
    获取资金流向信号
    返回: 'STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL'
    """
    try:
        df = adata.stock.market.baidu_capital_flow.get_capital_flow_min(stock_code=stock_code)
        df['trade_time'] = pd.to_datetime(df['trade_time'])
        
        # 获取最近5天的日级数据
        df['date'] = df['trade_time'].dt.date
        daily_flow = df.groupby('date').agg({
            'main_net_inflow': 'last',  # 收盘累计值
            'sm_net_inflow': 'last',
            'lg_net_inflow': 'last',
            'max_net_inflow': 'last'
        }).reset_index()
        
        if len(daily_flow) < 3:
            return 'NEUTRAL', 0
        
        # 计算最近3天的净流入变化
        recent = daily_flow.tail(3)
        main_flow_3d = recent['main_net_inflow'].diff().sum()
        
        # 转换为亿元（百度数据单位是分）
        main_flow_yi = main_flow_3d / 1e10
        
        # 判断信号
        if main_flow_yi > 5:
            return 'STRONG_BUY', main_flow_yi
        elif main_flow_yi > 1:
            return 'BUY', main_flow_yi
        elif main_flow_yi < -5:
            return 'STRONG_SELL', main_flow_yi
        elif main_flow_yi < -1:
            return 'SELL', main_flow_yi
        else:
            return 'NEUTRAL', main_flow_yi
            
    except Exception as e:
        print(f"获取资金流向失败: {e}")
        return 'NEUTRAL', 0

def generate_signals(df, stock_code: str):
    """
    生成综合交易信号
    结合 RSI + MACD + 资金流向
    """
    df = calculate_rsi(df)
    df = calculate_macd(df)
    
    # 获取资金流向信号
    flow_signal, flow_amount = get_capital_flow_signal(stock_code)
    
    df['signal'] = 'HOLD'
    df['signal_strength'] = 0
    
    for i in range(1, len(df)):
        rsi = df['RSI'].iloc[i]
        macd = df['MACD'].iloc[i]
        macd_prev = df['MACD'].iloc[i-1]
        
        # RSI 超卖 + MACD 金叉 + 资金流入 → 强买入
        if rsi < 30 and macd > 0 and macd_prev <= 0 and flow_signal in ['BUY', 'STRONG_BUY']:
            df.loc[i, 'signal'] = 'STRONG_BUY'
            df.loc[i, 'signal_strength'] = 3
        
        # RSI 超卖 + MACD 金叉 → 买入
        elif rsi < 30 and macd > 0 and macd_prev <= 0:
            df.loc[i, 'signal'] = 'BUY'
            df.loc[i, 'signal_strength'] = 2
        
        # RSI 超卖 → 观察
        elif rsi < 30:
            df.loc[i, 'signal'] = 'WATCH'
            df.loc[i, 'signal_strength'] = 1
        
        # RSI 超买 + MACD 死叉 + 资金流出 → 强卖出
        elif rsi > 70 and macd < 0 and macd_prev >= 0 and flow_signal in ['SELL', 'STRONG_SELL']:
            df.loc[i, 'signal'] = 'STRONG_SELL'
            df.loc[i, 'signal_strength'] = -3
        
        # RSI 超买 + MACD 死叉 → 卖出
        elif rsi > 70 and macd < 0 and macd_prev >= 0:
            df.loc[i, 'signal'] = 'SELL'
            df.loc[i, 'signal_strength'] = -2
        
        # RSI 超买 → 观察
        elif rsi > 70:
            df.loc[i, 'signal'] = 'OVERBOUGHT'
            df.loc[i, 'signal_strength'] = -1
    
    return df, flow_signal, flow_amount

def analyze_stock(stock_code: str, stock_name: str):
    """分析单只股票"""
    print(f"\n{'='*60}")
    print(f"📊 {stock_name} ({stock_code}) 综合分析")
    print(f"{'='*60}")
    
    # 获取数据
    df = get_stock_data(stock_code)
    
    # 生成信号
    df, flow_signal, flow_amount = generate_signals(df, stock_code)
    
    # 最新数据
    latest = df.iloc[-1]
    
    print(f"\n💰 最新价格: ¥{latest['close']:.2f} ({latest['pct_change']:+.2f}%)")
    print(f"📊 RSI(14): {latest['RSI']:.1f}")
    print(f"📈 MACD: {latest['MACD']:.3f}")
    print(f"💹 资金流向: {flow_signal} ({flow_amount:+.2f}亿)")
    
    # 判断当前状态
    print(f"\n🎯 当前状态:")
    if latest['RSI'] < 30:
        print(f"  ⚠️ RSI超卖 ({latest['RSI']:.1f} < 30)，可能存在反弹机会")
    elif latest['RSI'] > 70:
        print(f"  ⚠️ RSI超买 ({latest['RSI']:.1f} > 70)，注意回调风险")
    else:
        print(f"  ✅ RSI正常区间 ({latest['RSI']:.1f})")
    
    # 最近信号
    signals = df[df['signal'] != 'HOLD'].tail(5)
    if len(signals) > 0:
        print(f"\n📢 最近信号:")
        for _, row in signals.iterrows():
            emoji = {
                'STRONG_BUY': '🚀', 'BUY': '📈', 'WATCH': '👀',
                'STRONG_SELL': '🔻', 'SELL': '📉', 'OVERBOUGHT': '⚠️'
            }.get(row['signal'], '')
            print(f"  {emoji} {row['date'].strftime('%Y-%m-%d')}: {row['signal']} "
                  f"(RSI:{row['RSI']:.1f})")
    
    # 综合建议
    print(f"\n💡 综合建议:")
    if flow_signal in ['STRONG_BUY', 'BUY'] and latest['RSI'] < 50:
        print(f"  🟢 资金流入 + RSI偏低，关注买入机会")
    elif flow_signal in ['STRONG_SELL', 'SELL'] and latest['RSI'] > 50:
        print(f"  🔴 资金流出 + RSI偏高，注意风险")
    elif latest['RSI'] < 30:
        print(f"  🟡 RSI超卖，可观察等待确认")
    elif latest['RSI'] > 70:
        print(f"  🟡 RSI超买，不宜追高")
    else:
        print(f"  ⚪ 暂无明显信号，持有观望")
    
    return df

def main():
    """主函数"""
    # 分析自选股
    watchlist = [
        {"code": "000001", "name": "平安银行"},
        {"code": "600519", "name": "贵州茅台"},
        {"code": "600362", "name": "江西铜业"},
    ]
    
    print(f"🚀 RSI + 资金流向综合分析")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    for stock in watchlist:
        try:
            analyze_stock(stock["code"], stock["name"])
        except Exception as e:
            print(f"\n❌ {stock['name']} 分析失败: {e}")
    
    print(f"\n{'='*60}")
    print("分析完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
