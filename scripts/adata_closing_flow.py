#!/usr/bin/env python3
"""
尾盘资金流向监控 - 基于 adata (1nchaos)
实时监控自选股在 14:30-15:00 的资金流向
"""

import adata
from datetime import datetime, time
import pandas as pd
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# 自选股配置
WATCHLIST = [
    {"code": "002460", "name": "赣锋锂业", "market": "sz"},
    {"code": "002281", "name": "光迅科技", "market": "sz"},
    {"code": "601138", "name": "工业富联", "market": "sh"},
    {"code": "002171", "name": "楚江新材", "market": "sz"},
]

def get_closing_flow(stock_code: str, date_str: str = None):
    """
    获取指定股票尾盘（14:30-15:00）的资金流向
    
    Returns:
        DataFrame with columns:
        - trade_time: 交易时间
        - main_net_inflow: 主力净流入
        - sm_net_inflow: 小单净流入
        - mid_net_inflow: 中单净流入
        - lg_net_inflow: 大单净流入
        - max_net_inflow: 超大单净流入
    """
    try:
        # 获取分钟级资金流向（使用百度数据源）
        df = adata.stock.market.baidu_capital_flow.get_capital_flow_min(stock_code=stock_code)
        
        if df is None or df.empty:
            return None
        
        # 过滤尾盘时间 14:30-15:00
        df['trade_time'] = pd.to_datetime(df['trade_time'])
        df['time_only'] = df['trade_time'].dt.time
        
        closing_start = time(14, 30)
        closing_end = time(15, 0)
        
        closing_df = df[(df['time_only'] >= closing_start) & (df['time_only'] <= closing_end)]
        
        return closing_df
        
    except Exception as e:
        print(f"获取 {stock_code} 资金流向失败: {e}")
        return None

def analyze_closing_flow(df, stock_name: str):
    """分析尾盘资金流向并生成报告"""
    if df is None or df.empty:
        return None
    
    # 计算尾盘资金流向（累计值相减）
    first_row = df.iloc[0]
    last_row = df.iloc[-1]
    
    # 尾盘净流入 = 收盘累计 - 开盘累计
    total_main = last_row['main_net_inflow'] - first_row['main_net_inflow']
    total_sm = last_row['sm_net_inflow'] - first_row['sm_net_inflow']
    total_mid = last_row['mid_net_inflow'] - first_row['mid_net_inflow']
    total_lg = last_row['lg_net_inflow'] - first_row['lg_net_inflow']
    total_max = last_row['max_net_inflow'] - first_row['max_net_inflow']
    
    # 转换为万元（原始数据单位是元）
    def to_wan(x):
        return f"{x/10000:.1f}万"
    
    report = {
        "name": stock_name,
        "total_main": total_main,
        "total_sm": total_sm,
        "total_lg": total_lg,
        "total_max": total_max,
        "flow_emoji": "🔴" if total_main > 0 else "🟢",
        "signal": "流入" if total_main > 0 else "流出"
    }
    
    return report

def generate_report(date_str: str = None):
    """生成所有自选股的尾盘资金流向报告"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    reports = []
    
    print(f"\n{'='*60}")
    print(f"📊 尾盘资金流向报告 - {date_str}")
    print(f"{'='*60}\n")
    
    for stock in WATCHLIST:
        code = stock["code"]
        name = stock["name"]
        
        print(f"获取 {name}({code}) 数据...", end=" ")
        df = get_closing_flow(code, date_str)
        
        if df is not None and not df.empty:
            report = analyze_closing_flow(df, name)
            if report:
                reports.append(report)
                print("✅")
        else:
            print("❌")
    
    return reports

def format_message(reports):
    """格式化飞书消息"""
    if not reports:
        return "暂无数据"
    
    now = datetime.now().strftime("%H:%M")
    msg = f"📊 **尾盘资金流向报告** ({now})\n\n"
    
    # 按主力净流入排序
    reports_sorted = sorted(reports, key=lambda x: x['total_main'], reverse=True)
    
    for r in reports_sorted:
        name = r['name']
        emoji = r['flow_emoji']
        signal = r['signal']
        # 百度数据单位是分，转换为亿元
        main_yi = r['total_main'] / 1e10
        max_yi = r['total_max'] / 1e10
        
        msg += f"**{name}**\n"
        msg += f"  主力: {emoji} {main_yi:+.2f}亿 ({signal})\n"
        msg += f"  超大单: {max_yi:+.2f}亿\n\n"
    
    # 添加简评
    inflow_stocks = [r for r in reports if r['total_main'] > 0]
    outflow_stocks = [r for r in reports if r['total_main'] < 0]
    
    msg += "**💡 简评**\n"
    msg += f"• 主力流入: {len(inflow_stocks)} 只\n"
    msg += f"• 主力流出: {len(outflow_stocks)} 只\n"
    
    if inflow_stocks:
        top_in = max(inflow_stocks, key=lambda x: x['total_main'])
        msg += f"• 流入最多: {top_in['name']} (+{top_in['total_main']/1e10:.2f}亿)\n"
    
    return msg

def main():
    """主函数"""
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查是否在尾盘时段
    now_time = datetime.now().time()
    closing_start = time(14, 30)
    closing_end = time(15, 0)
    
    if closing_start <= now_time <= closing_end:
        print("✅ 当前是尾盘监控时段 (14:30-15:00)")
    else:
        print(f"ℹ️ 非尾盘时段，获取昨日数据供参考")
    
    # 生成报告
    reports = generate_report()
    
    if reports:
        message = format_message(reports)
        print("\n" + "="*60)
        print(message)
        print("="*60)
        
        # 保存到文件
        output_dir = os.path.expanduser("~/.openclaw/workspace/data")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "adata_closing_flow.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(message)
        
        print(f"\n✅ 报告已保存: {output_file}")
        return message
    else:
        print("❌ 未获取到任何数据")
        return None

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
