#!/usr/bin/env python3
"""
尾盘资金流向监控 + 飞书通知
使用 AkShare 获取东方财富数据
简化版：只使用稳定可用的大盘资金流向接口
"""

import akshare as ak
import pandas as pd
from datetime import datetime, time
import sys
import os
import warnings
warnings.filterwarnings('ignore')

def get_market_flow():
    """获取大盘资金流向（最稳定的接口）"""
    try:
        df = ak.stock_market_fund_flow()
        # 取最新一天的数据
        latest = df.iloc[0]
        return latest
    except Exception as e:
        print(f"获取大盘资金流向失败: {e}")
        return None

def get_individual_flow(code: str, market: str = "sh"):
    """获取个股资金流向"""
    try:
        df = ak.stock_individual_fund_flow(stock=code, market=market)
        return df.head(3)  # 最近3天
    except Exception as e:
        print(f"获取个股{code}资金流向失败: {e}")
        return None

def format_flow_report(market_data, watchlist=None):
    """格式化资金流向报告"""
    if market_data is None:
        return "❌ 获取数据失败"
    
    now = datetime.now().strftime("%H:%M")
    date = market_data.get('日期', '未知')
    
    msg = f"📊 **尾盘资金流向报告** ({now})\n"
    msg += f"📅 数据日期: {date}\n\n"
    
    # 大盘概况
    sh_close = market_data.get('上证-收盘价', 0)
    sh_change = market_data.get('上证-涨跌幅', 0)
    sz_close = market_data.get('深证-收盘价', 0)
    sz_change = market_data.get('深证-涨跌幅', 0)
    
    sh_emoji = "🔴" if sh_change >= 0 else "🟢"
    sz_emoji = "🔴" if sz_change >= 0 else "🟢"
    
    msg += "**📈 大盘表现**\n"
    msg += f"• 上证: {sh_close} {sh_emoji} {sh_change:+.2f}%\n"
    msg += f"• 深证: {sz_close} {sz_emoji} {sz_change:+.2f}%\n\n"
    
    # 资金流向（单位：亿元）
    msg += "**💰 资金流向（亿元）**\n"
    
    # 主力净流入
    main_in = market_data.get('主力净流入-净额', 0) / 1e8
    main_pct = market_data.get('主力净流入-净占比', 0)
    main_emoji = "🔴流入" if main_in > 0 else "🟢流出"
    msg += f"• 主力资金: {main_emoji} {abs(main_in):.1f}亿 ({main_pct:+.2f}%)\n"
    
    # 超大单
    super_in = market_data.get('超大单净流入-净额', 0) / 1e8
    super_pct = market_data.get('超大单净流入-净占比', 0)
    super_emoji = "🔴" if super_in > 0 else "🟢"
    msg += f"• 超大单: {super_emoji} {super_in:+.1f}亿 ({super_pct:+.2f}%)\n"
    
    # 大单
    big_in = market_data.get('大单净流入-净额', 0) / 1e8
    big_pct = market_data.get('大单净流入-净占比', 0)
    big_emoji = "🔴" if big_in > 0 else "🟢"
    msg += f"• 大单: {big_emoji} {big_in:+.1f}亿 ({big_pct:+.2f}%)\n"
    
    # 中单
    mid_in = market_data.get('中单净流入-净额', 0) / 1e8
    mid_pct = market_data.get('中单净流入-净占比', 0)
    mid_emoji = "🔴" if mid_in > 0 else "🟢"
    msg += f"• 中单: {mid_emoji} {mid_in:+.1f}亿 ({mid_pct:+.2f}%)\n"
    
    # 小单（散户）
    small_in = market_data.get('小单净流入-净额', 0) / 1e8
    small_pct = market_data.get('小单净流入-净占比', 0)
    small_emoji = "🔴流入" if small_in > 0 else "🟢流出"
    msg += f"• 散户资金: {small_emoji} {abs(small_in):.1f}亿 ({small_pct:+.2f}%)\n\n"
    
    # 解读
    msg += "**💡 简评**\n"
    if main_in > 0:
        msg += "✅ 主力资金净流入，态度偏多\n"
    else:
        msg += "⚠️ 主力资金净流出，态度偏空\n"
    
    if super_in > 0 and main_in > 0:
        msg += "🚀 超大单+主力双流入，尾盘抢筹信号"
    elif super_in < 0 and main_in < 0:
        msg += "📉 大资金流出，注意次日风险"
    
    return msg

def main():
    """主函数"""
    print("="*60)
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 检查是否在尾盘时间
    now_time = datetime.now().time()
    if time(14, 30) <= now_time <= time(15, 0):
        print("✅ 尾盘监控时段 (14:30-15:00)\n")
    else:
        print("ℹ️ 非尾盘时段，获取最新数据供参考...\n")
    
    # 获取数据
    market_data = get_market_flow()
    
    if market_data is not None:
        # 格式化消息
        message = format_flow_report(market_data)
        print("\n" + "="*60)
        print(message)
        print("="*60)
        
        # 保存到文件
        output_dir = os.path.expanduser("~/.openclaw/workspace/data")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "closing_flow_report.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(message)
        
        print(f"\n✅ 报告已保存: {output_file}")
        return message
    else:
        print("❌ 获取数据失败")
        return None

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
