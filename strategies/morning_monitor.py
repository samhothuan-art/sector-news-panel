#!/usr/bin/env python3
"""
早盘异动实时监控脚本
监控时段: 9:30-10:00 (早盘黄金30分钟)
监控频率: 每5分钟
推送方式: 飞书通知
"""

import requests
import pandas as pd
from datetime import datetime, time
import time as time_module
import json
import sys
import os

# ============ 配置 ============

# 自选股列表
WATCHLIST = [
    {"code": "000001", "name": "平安银行", "market": "sz"},
    {"code": "600519", "name": "贵州茅台", "market": "sh"},
    {"code": "000858", "name": "五粮液", "market": "sz"},
    {"code": "600362", "name": "江西铜业", "market": "sh"},
    {"code": "601318", "name": "中国平安", "market": "sh"},
]

# 异动阈值
THRESHOLDS = {
    "price_change_pct": 2.0,  # 涨幅超过2%
    "volume_ratio": 1.5,      # 量比超过1.5倍
    "turnover_min": 1.0,      # 成交额至少1亿
}

# 监控时间
MONITOR_START = time(9, 30)
MONITOR_END = time(10, 0)
CHECK_INTERVAL = 300  # 5分钟 = 300秒

# ============ 新浪财经实时行情 ============

def get_sina_realtime_quotes(codes):
    """
    获取新浪财经实时行情
    
    Args:
        codes: 股票代码列表，如 ["sh600519", "sz000001"]
    
    Returns:
        DataFrame with realtime data
    """
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    
    try:
        response = requests.get(url, timeout=10, headers={
            'Referer': 'https://finance.sina.com.cn',
            'User-Agent': 'Mozilla/5.0'
        })
        
        if response.status_code != 200:
            return None
        
        data = []
        lines = response.text.strip().split('\n')
        
        for line in lines:
            if not line or '=' not in line:
                continue
            
            code_part, data_part = line.split('=')
            code = code_part.replace('var hq_str_', '').strip()
            
            if not data_part or data_part == '""':
                continue
            
            # 解析数据
            fields = data_part.strip('";').split(',')
            
            if len(fields) < 33:
                continue
            
            # 根据市场解析字段
            if code.startswith('sh'):
                # 上海市场格式
                data.append({
                    'code': code[2:],  # 去掉 sh/sz
                    'full_code': code,
                    'name': fields[0],
                    'open': float(fields[1]) if fields[1] else 0,
                    'close_yesterday': float(fields[2]) if fields[2] else 0,
                    'price': float(fields[3]) if fields[3] else 0,
                    'high': float(fields[4]) if fields[4] else 0,
                    'low': float(fields[5]) if fields[5] else 0,
                    'bid': float(fields[6]) if fields[6] else 0,
                    'ask': float(fields[7]) if fields[7] else 0,
                    'volume': int(fields[8]) if fields[8] else 0,
                    'amount': float(fields[9]) if fields[9] else 0,
                    'date': fields[30],
                    'time': fields[31],
                })
            else:
                # 深圳市场格式
                data.append({
                    'code': code[2:],
                    'full_code': code,
                    'name': fields[0],
                    'open': float(fields[1]) if fields[1] else 0,
                    'close_yesterday': float(fields[2]) if fields[2] else 0,
                    'price': float(fields[3]) if fields[3] else 0,
                    'high': float(fields[4]) if fields[4] else 0,
                    'low': float(fields[5]) if fields[5] else 0,
                    'bid': float(fields[6]) if fields[6] else 0,
                    'ask': float(fields[7]) if fields[7] else 0,
                    'volume': int(fields[8]) if fields[8] else 0,
                    'amount': float(fields[9]) if fields[9] else 0,
                    'date': fields[30],
                    'time': fields[31],
                })
        
        df = pd.DataFrame(data)
        
        # 计算涨跌幅
        if not df.empty and 'close_yesterday' in df.columns:
            df['change_pct'] = ((df['price'] - df['close_yesterday']) / df['close_yesterday'] * 100).round(2)
        
        return df
        
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return None

# ============ 历史数据获取（用于计算量比） ============

def get_prev_day_volume(code, market):
    """获取昨日成交量（用于计算量比）"""
    # 这里简化处理，实际应该查询历史数据
    # 返回一个默认值
    return None

# ============ 异动检测 ============

def detect_abnormal(df, prev_data=None):
    """
    检测异动股票
    
    Returns:
        list of dict with abnormal stocks
    """
    if df is None or df.empty:
        return []
    
    abnormal = []
    
    for _, row in df.iterrows():
        signals = []
        
        # 检查涨幅
        if row['change_pct'] >= THRESHOLDS['price_change_pct']:
            signals.append(f"涨{row['change_pct']:.1f}%")
        
        # 检查成交额
        amount_yi = row['amount'] / 100000000  # 转换为亿
        if amount_yi >= THRESHOLDS['turnover_min']:
            signals.append(f"成交{amount_yi:.1f}亿")
        
        # 如果有信号，添加到列表
        if signals:
            abnormal.append({
                'code': row['code'],
                'name': row['name'],
                'price': row['price'],
                'change_pct': row['change_pct'],
                'amount_yi': amount_yi,
                'high': row['high'],
                'low': row['low'],
                'time': row['time'],
                'signals': signals,
            })
    
    # 按涨幅排序
    abnormal.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return abnormal

# ============ 飞书推送 ============

def format_feishu_message(abnormal, check_time):
    """格式化飞书消息"""
    if not abnormal:
        return None
    
    msg = f"🚀 **早盘异动提醒** ({check_time})\n\n"
    
    for stock in abnormal:
        emoji = "🔴" if stock['change_pct'] > 0 else "🟢"
        msg += f"**{stock['name']} ({stock['code']})**\n"
        msg += f"  价格: ¥{stock['price']:.2f} {emoji} {stock['change_pct']:+.2f}%\n"
        msg += f"  成交: {stock['amount_yi']:.1f}亿\n"
        msg += f"  信号: {', '.join(stock['signals'])}\n"
        msg += f"  时间: {stock['time']}\n\n"
    
    msg += "💡 **建议**: 关注资金是否配合，确认突破有效性"
    
    return msg

def send_feishu_message(message):
    """发送飞书消息"""
    # 这里简化处理，实际应该调用飞书API
    # 可以保存到文件，让其他服务读取推送
    
    output_dir = os.path.expanduser("~/.openclaw/workspace/data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存到文件
    timestamp = datetime.now().strftime("%H%M%S")
    file_path = os.path.join(output_dir, f"alert_{timestamp}.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"✅ 消息已保存: {file_path}")
    
    # 同时打印到控制台
    print("\n" + "="*60)
    print("飞书消息预览:")
    print("="*60)
    print(message)
    print("="*60 + "\n")

# ============ 主监控循环 ============

def check_once():
    """执行一次检查"""
    # 准备股票代码
    codes = [f"{s['market']}{s['code']}" for s in WATCHLIST]
    
    # 获取实时行情
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取实时行情...")
    df = get_sina_realtime_quotes(codes)
    
    if df is None or df.empty:
        print("❌ 获取数据失败")
        return
    
    print(f"✅ 获取 {len(df)} 只股票数据")
    
    # 检测异动
    abnormal = detect_abnormal(df)
    
    if abnormal:
        print(f"🚨 发现 {len(abnormal)} 只异动股票")
        
        # 格式化消息
        message = format_feishu_message(abnormal, datetime.now().strftime("%H:%M"))
        
        # 发送通知
        if message:
            send_feishu_message(message)
    else:
        print("✅ 暂无异动")

def monitor_loop():
    """监控主循环"""
    print("="*60)
    print("🚀 早盘异动监控启动")
    print(f"监控时段: {MONITOR_START.strftime('%H:%M')} - {MONITOR_END.strftime('%H:%M')}")
    print(f"检查间隔: {CHECK_INTERVAL}秒")
    print(f"监控股票: {len(WATCHLIST)}只")
    print("="*60 + "\n")
    
    # 检查是否在监控时段
    now = datetime.now().time()
    
    if now < MONITOR_START:
        # 等待开盘
        wait_seconds = (datetime.combine(datetime.today(), MONITOR_START) - 
                       datetime.now()).total_seconds()
        print(f"⏳ 等待开盘，还有 {wait_seconds:.0f} 秒...")
        time_module.sleep(max(0, wait_seconds))
    
    # 开始监控
    check_count = 0
    
    while datetime.now().time() <= MONITOR_END:
        check_count += 1
        print(f"\n{'='*60}")
        print(f"📊 第 {check_count} 次检查 ({datetime.now().strftime('%H:%M:%S')})")
        print(f"{'='*60}")
        
        try:
            check_once()
        except Exception as e:
            print(f"❌ 检查异常: {e}")
        
        # 等待下一次检查
        if datetime.now().time() < MONITOR_END:
            print(f"⏳ 等待 {CHECK_INTERVAL} 秒后再次检查...")
            time_module.sleep(CHECK_INTERVAL)
        else:
            break
    
    print("\n" + "="*60)
    print("✅ 早盘监控结束")
    print("="*60)

def main():
    """主函数"""
    # 检查当前时间
    now = datetime.now()
    
    print(f"🕐 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试模式：如果不在监控时段，直接运行一次测试
    if now.time() < MONITOR_START or now.time() > MONITOR_END:
        print("\n⚠️ 不在监控时段（9:30-10:00），运行测试模式...\n")
        check_once()
    else:
        # 正常运行监控循环
        monitor_loop()

if __name__ == "__main__":
    main()
