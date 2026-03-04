#!/usr/bin/env python3
"""
尾盘资金流向监控 + 飞书通知
实时监控 14:30-15:00 的资金动向
"""

import akshare as ak
import pandas as pd
from datetime import datetime, time
import sys
import os

# 添加 workspace 路径
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace"))

def get_closing_flow_summary():
    """获取尾盘资金流向汇总"""
    try:
        # 1. 大盘资金流向
        market_df = ak.stock_market_fund_flow()
        
        # 2. 行业板块资金流向
        sector_df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        
        # 3. 概念板块资金流向
        concept_df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="概念资金流")
        
        summary = {
            "time": datetime.now().strftime("%H:%M"),
            "market": market_df,
            "top_sectors_in": sector_df.head(5) if sector_df is not None else None,
            "top_sectors_out": sector_df.tail(5) if sector_df is not None else None,
            "top_concepts_in": concept_df.head(5) if concept_df is not None else None,
        }
        
        return summary
        
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

def format_flow_message(summary):
    """格式化资金流向为飞书消息"""
    if not summary:
        return "获取资金流向数据失败"
    
    time_str = summary["time"]
    msg = f"📊 **尾盘资金流向报告** ({time_str})\n\n"
    
    # 市场整体
    if summary["market"] is not None:
        market = summary["market"]
        msg += "**💰 大盘资金概况**\n"
        for _, row in market.iterrows():
            name = row.get('名称', '未知')
            # 根据正负显示颜色（用 emoji 表示）
            main_in = row.get('主力净流入', 0)
            if isinstance(main_in, (int, float)):
                emoji = "🔴" if main_in > 0 else "🟢"
                msg += f"• {name}: {emoji} {main_in/10000:.1f}亿\n"
        msg += "\n"
    
    # 流入板块
    if summary["top_sectors_in"] is not None:
        msg += "**📈 资金流入 TOP5 行业**\n"
        for i, row in summary["top_sectors_in"].iterrows():
            name = row.get('名称', '未知')
            amount = row.get('主力净流入', 0)
            if isinstance(amount, (int, float)):
                msg += f"{i+1}. {name}: +{amount/10000:.1f}亿 🔴\n"
        msg += "\n"
    
    # 流出板块
    if summary["top_sectors_out"] is not None:
        msg += "**📉 资金流出 TOP5 行业**\n"
        sectors = summary["top_sectors_out"].iloc[::-1]  # 反转，从大到小
        for i, row in sectors.iterrows():
            name = row.get('名称', '未知')
            amount = row.get('主力净流入', 0)
            if isinstance(amount, (int, float)):
                msg += f"{i+1}. {name}: {amount/10000:.1f}亿 🟢\n"
        msg += "\n"
    
    # 概念板块
    if summary["top_concepts_in"] is not None:
        msg += "**💡 热门概念资金流入**\n"
        for i, row in summary["top_concepts_in"].head(3).iterrows():
            name = row.get('名称', '未知')
            amount = row.get('主力净流入', 0)
            if isinstance(amount, (int, float)):
                msg += f"• {name}: +{amount/10000:.1f}亿\n"
    
    msg += "\n💡 **解读**: 尾盘资金流向反映主力资金对次日态度"
    
    return msg

def is_closing_time():
    """判断是否在尾盘时间（14:30-15:00）"""
    now = datetime.now().time()
    return time(14, 30) <= now <= time(15, 0)

def main():
    """主函数"""
    print("="*60)
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 检查是否在尾盘时间
    if not is_closing_time():
        print("⚠️ 不在尾盘监控时段 (14:30-15:00)")
        print("继续获取数据供参考...\n")
    else:
        print("✅ 尾盘监控时段\n")
    
    # 获取数据
    summary = get_closing_flow_summary()
    
    if summary:
        # 打印到控制台
        message = format_flow_message(summary)
        print(message)
        
        # 保存到文件（可以后续发送到飞书）
        output_file = os.path.expanduser("~/.openclaw/workspace/data/closing_flow_report.txt")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(message)
        
        print(f"\n✅ 报告已保存到: {output_file}")
        
        # 返回消息供飞书发送
        return message
    else:
        print("❌ 获取数据失败")
        return None

if __name__ == "__main__":
    main()
