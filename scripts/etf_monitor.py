#!/usr/bin/env python3
"""
ETF持仓监控预警脚本
监控工业母机ETF、半导体ETF、券商ETF的异动
"""

import urllib.request
import re
from datetime import datetime

# ETF监控配置
ETF_WATCHLIST = [
    {"code": "159667", "name": "工业母机ETF", "cost": 1.938, "shares": 1700, "alert_up": 5, "alert_down": -3},
    {"code": "512480", "name": "半导体ETF", "cost": 1.617, "shares": 2600, "alert_up": 5, "alert_down": -3},
    {"code": "512000", "name": "券商ETF", "cost": 0.559, "shares": 10000, "alert_up": 5, "alert_down": -3},
]

def get_etf_price(code):
    """获取ETF实时价格"""
    if code.startswith(('5', '1')):
        prefix = 'sh'
    else:
        prefix = 'sz'
    
    try:
        url = f'http://qt.gtimg.cn/q={prefix}{code}'
        response = urllib.request.urlopen(url, timeout=5)
        data = response.read().decode('gbk')
        
        match = re.search(rf'v_{prefix}{code}="(.*?)"', data)
        if match:
            fields = match.group(1).split('~')
            return {
                'name': fields[1],
                'price': float(fields[3]),
                'change_pct': float(fields[32]),
                'prev_close': float(fields[4]),
            }
    except Exception as e:
        print(f"获取{code}失败: {e}")
    return None

def check_alerts():
    """检查预警条件"""
    print(f"📊 ETF持仓监控 - {datetime.now().strftime('%H:%M')}\n")
    print("="*60)
    
    alerts = []
    
    for etf in ETF_WATCHLIST:
        data = get_etf_price(etf['code'])
        if not data:
            continue
        
        # 计算盈亏
        current_value = data['price'] * etf['shares']
        cost_value = etf['cost'] * etf['shares']
        pnl_pct = (data['price'] - etf['cost']) / etf['cost'] * 100
        pnl_amount = current_value - cost_value
        
        # 检查预警
        alert_msg = None
        if pnl_pct >= etf['alert_up']:
            alert_msg = f"🔴 {etf['name']} 盈利超{etf['alert_up']}%: {pnl_pct:.2f}%"
        elif pnl_pct <= etf['alert_down']:
            alert_msg = f"🟢 {etf['name']} 亏损超{abs(etf['alert_down'])}%: {pnl_pct:.2f}%"
        
        if alert_msg:
            alerts.append(alert_msg)
        
        # 打印状态
        emoji = "📈" if pnl_pct >= 0 else "📉"
        print(f"\n{etf['name']} ({etf['code']})")
        print(f"  现价: {data['price']:.3f} | 成本: {etf['cost']:.3f}")
        print(f"  持仓盈亏: {emoji} {pnl_pct:+.2f}% ({pnl_amount:+.2f}元)")
        print(f"  今日涨跌: {data['change_pct']:+.2f}%")
    
    print("\n" + "="*60)
    
    if alerts:
        print("\n⚠️ 预警触发:")
        for alert in alerts:
            print(f"  {alert}")
    else:
        print("\n✅ 无预警，持仓正常")
    
    return alerts

if __name__ == "__main__":
    check_alerts()
