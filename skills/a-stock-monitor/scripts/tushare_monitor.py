#!/usr/bin/env python3
"""
Tushare实时监控脚本 - 尾盘抢筹助手
使用：日线RT + 申万行业 + 新浪财经补充
"""

import tushare as ts
import requests
import json
from datetime import datetime

# 配置
TOKEN = '9e002cf5c323daadf44e180b80ae9489a543a5709f05edf1609e377d'
ts.set_token(TOKEN)
pro = ts.pro_api()

# 十大核心板块申万代码
SECTORS = {
    'AI算力': '801080',      # 电子
    '半导体': '801080',      # 电子
    '机器人': '801880',      # 机械设备
    '有色金属': '801050',    # 有色金属
    '新能源': '801730',      # 电力设备
    '消费': '801110',        # 家用电器
    '军工': '801740',        # 国防军工
    '高股息': '801030',      # 煤炭
    '工业母机': '801880',    # 机械设备
    '电网电力': '801730',    # 电力设备
}

# 持仓股
HOLDINGS = {
    '600406.SH': '国电南瑞',
    '600863.SH': '内蒙华电',
}

def get_realtime_price(code):
    """获取实时价格（Tushare日线RT）"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        df = pro.daily(ts_code=code, start_date=today, end_date=today)
        if df is not None and not df.empty:
            row = df.iloc[0]
            return {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'pre_close': row['pre_close'],
                'change_pct': (row['close'] - row['pre_close']) / row['pre_close'] * 100,
                'vol': row['vol'],
                'amount': row['amount']
            }
    except Exception as e:
        print(f"Tushare获取失败: {e}")
    return None

def get_sina_price(code):
    """新浪财经备用"""
    try:
        prefix = 'sh' if code.startswith('6') else 'sz'
        url = f'https://hq.sinajs.cn/list={prefix}{code[:6]}'
        r = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'}, timeout=5)
        r.encoding = 'gb2312'
        data = r.text.split('"')[1].split(',')
        if len(data) >= 32:
            return {
                'name': data[0],
                'open': float(data[1]),
                'pre_close': float(data[2]),
                'close': float(data[3]),
                'high': float(data[4]),
                'low': float(data[5]),
                'change_pct': (float(data[3]) - float(data[2])) / float(data[2]) * 100
            }
    except:
        pass
    return None

def monitor_holdings():
    """监控持仓股"""
    print("📊 持仓股实时监控")
    print("=" * 60)
    
    for code, name in HOLDINGS.items():
        # 先尝试Tushare
        data = get_realtime_price(code)
        source = "Tushare"
        
        # 失败则用新浪财经
        if data is None:
            data = get_sina_price(code)
            source = "新浪财经"
        
        if data:
            emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
            print(f"{emoji} {name} ({code})")
            print(f"   现价: ¥{data['close']:.2f} ({data['change_pct']:+.2f}%)")
            print(f"   最高: ¥{data['high']:.2f} 最低: ¥{data['low']:.2f}")
            print(f"   成交: {data.get('vol', 0)/10000:.1f}万手")
            print(f"   来源: {source}")
            print()

def monitor_sectors():
    """监控板块（申万+新浪补充）"""
    print("📈 十大板块监控")
    print("=" * 60)
    
    # 板块代表股
    sector_leaders = {
        'AI算力': '300308',
        '半导体': '002371',
        '机器人': '688017',
        '有色金属': '600111',
        '新能源': '002594',
        '消费': '600519',
        '军工': '002025',
        '高股息': '600028',
        '工业母机': '601882',
        '电网电力': '600406',
    }
    
    results = []
    for sector, code in sector_leaders.items():
        data = get_sina_price(code)
        if data:
            results.append((sector, code, data['change_pct']))
    
    # 排序
    results.sort(key=lambda x: x[2], reverse=True)
    
    print("\n板块涨跌排名:")
    for sector, code, pct in results:
        emoji = "🟢" if pct >= 0 else "🔴"
        star = "⭐" if 2 <= pct <= 5 else ""
        print(f"{emoji} {sector:10s}: {pct:+6.2f}% {star}")

def main():
    print(f"🚀 Tushare实时监控启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    monitor_holdings()
    print()
    monitor_sectors()
    
    print("\n" + "=" * 60)
    print("监控完成！")

if __name__ == "__main__":
    main()
