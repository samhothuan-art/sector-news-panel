#!/usr/bin/env python3
"""
尾盘资金流向监控脚本
使用 AkShare 获取东方财富的实时资金流向数据
"""

import akshare as ak
from datetime import datetime
import json

def get_market_capital_flow():
    """获取市场整体资金流向（主力/散户/小单等）"""
    try:
        # 获取当日资金流向统计
        df = ak.stock_market_activity_legu()
        print("="*50)
        print(f"📊 市场整体资金流向 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*50)
        print(df.to_string())
        return df
    except Exception as e:
        print(f"获取市场资金流向失败: {e}")
        return None

def get_sector_capital_flow():
    """获取行业板块资金流向"""
    try:
        # 行业板块资金流向
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        print("\n" + "="*50)
        print("🏭 行业板块资金流向 TOP10")
        print("="*50)
        print(df.head(10).to_string())
        return df
    except Exception as e:
        print(f"获取板块资金流向失败: {e}")
        return None

def get_individual_capital_flow(code: str, market: str = "sh"):
    """
    获取个股资金流向
    :param code: 股票代码，如 "600362"
    :param market: 市场，sh/sz/bj
    """
    try:
        # 个股资金流
        df = ak.stock_individual_fund_flow(stock=code, market=market)
        print("\n" + "="*50)
        print(f"📈 个股资金流向 - {code}")
        print("="*50)
        print(df.head(5).to_string())
        return df
    except Exception as e:
        print(f"获取个股资金流向失败: {e}")
        return None

def get_realtime_capital_flow():
    """获取实时资金流向（当日累计）"""
    try:
        # 获取大盘资金流向实时数据
        df = ak.stock_market_fund_flow()
        print("\n" + "="*50)
        print(f"💰 实时资金流向 - {datetime.now().strftime('%H:%M')}")
        print("="*50)
        print(df.to_string())
        return df
    except Exception as e:
        print(f"获取实时资金流向失败: {e}")
        return None

def analyze_closing_flow():
    """
    尾盘资金流向分析（14:30-15:00）
    监控最后30分钟的资金动向
    """
    now = datetime.now()
    
    # 获取实时数据
    market_flow = get_market_capital_flow()
    sector_flow = get_sector_capital_flow()
    
    if market_flow is not None:
        print("\n" + "="*50)
        print("🎯 尾盘分析要点:")
        print("="*50)
        print("""
1. 主力资金流向：正值表示净流入，负值表示流出
2. 散户资金流向：通常与主力反向
3. 大单动向：大单净流入通常预示短期走势
4. 板块轮动：关注资金流入的行业板块
        """)
    
    return market_flow, sector_flow

if __name__ == "__main__":
    print("🔍 开始获取资金流向数据...\n")
    
    # 获取市场整体资金
    analyze_closing_flow()
    
    # 示例：获取个股资金流向
    # get_individual_capital_flow("600362", "sh")
