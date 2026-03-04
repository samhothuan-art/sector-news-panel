#!/usr/bin/env python3
"""
早盘异动监控 + 飞书推送
实时监控并推送到飞书
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace"))

from strategies.morning_monitor import check_once, MONITOR_START, MONITOR_END, send_feishu_message
from datetime import datetime, time
import time as time_module
from message import send as feishu_send

def check_and_notify():
    """检查并发送飞书通知"""
    from strategies.morning_monitor import (
        get_sina_realtime_quotes, detect_abnormal, format_feishu_message, WATCHLIST
    )
    
    # 准备股票代码
    codes = [f"{s['market']}{s['code']}" for s in WATCHLIST]
    
    # 获取实时行情
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取实时行情...")
    df = get_sina_realtime_quotes(codes)
    
    if df is None or df.empty:
        print("❌ 获取数据失败")
        return False
    
    print(f"✅ 获取 {len(df)} 只股票数据")
    
    # 显示所有股票状态
    print("\n📊 当前行情:")
    for _, row in df.iterrows():
        emoji = "🔴" if row['change_pct'] > 0 else "🟢" if row['change_pct'] < 0 else "⚪"
        print(f"  {row['name']}: ¥{row['price']:.2f} {emoji} {row['change_pct']:+.2f}%")
    
    # 检测异动
    abnormal = detect_abnormal(df)
    
    if abnormal:
        print(f"\n🚨 发现 {len(abnormal)} 只异动股票")
        
        # 格式化消息
        message = format_feishu_message(abnormal, datetime.now().strftime("%H:%M"))
        
        if message:
            # 发送到飞书
            try:
                feishu_send(message=message)
                print("✅ 飞书通知已发送")
            except Exception as e:
                print(f"❌ 飞书发送失败: {e}")
                # 保存到文件
                output_dir = os.path.expanduser("~/.openclaw/workspace/data")
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%H%M%S")
                with open(f"{output_dir}/alert_{timestamp}.txt", 'w') as f:
                    f.write(message)
        
        return True
    else:
        print("✅ 暂无异动")
        return False

def main():
    """主函数"""
    now = datetime.now()
    print(f"🚀 早盘监控 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_and_notify()
    
    print("\n完成")

if __name__ == "__main__":
    main()
