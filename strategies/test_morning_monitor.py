#!/usr/bin/env python3
"""
测试早盘监控系统
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace"))

from strategies.morning_monitor import get_sina_realtime_quotes, detect_abnormal, format_feishu_message, WATCHLIST
from datetime import datetime

print("="*60)
print("🧪 早盘监控系统测试")
print("="*60)

# 准备股票代码
codes = [f"{s['market']}{s['code']}" for s in WATCHLIST]

print(f"\n📋 监控股票列表:")
for s in WATCHLIST:
    print(f"  • {s['name']} ({s['code']})")

print(f"\n🌐 测试获取实时行情...")
df = get_sina_realtime_quotes(codes)

if df is None:
    print("❌ 获取数据失败")
    sys.exit(1)

print(f"✅ 成功获取 {len(df)} 只股票数据")

print(f"\n📊 当前行情:")
for _, row in df.iterrows():
    emoji = "🔴" if row['change_pct'] > 0 else "🟢" if row['change_pct'] < 0 else "⚪"
    print(f"  {row['name']}: ¥{row['price']:.2f} {emoji} {row['change_pct']:+.2f}% | 成交 {row['amount']/1e8:.1f}亿")

print(f"\n🔍 检测异动...")
abnormal = detect_abnormal(df)

if abnormal:
    print(f"🚨 发现 {len(abnormal)} 只异动股票")
    
    message = format_feishu_message(abnormal, datetime.now().strftime("%H:%M"))
    
    print(f"\n📱 飞书消息预览:")
    print("-"*60)
    print(message)
    print("-"*60)
    
    # 询问是否发送测试消息
    response = input("\n是否发送测试消息到飞书? (y/n): ")
    if response.lower() == 'y':
        try:
            from message import send as feishu_send
            feishu_send(message=message)
            print("✅ 测试消息已发送")
        except Exception as e:
            print(f"❌ 发送失败: {e}")
else:
    print("✅ 暂无异动股票")

print(f"\n✅ 测试完成")
print("="*60)
