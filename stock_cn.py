#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股实时行情查询脚本
使用腾讯财经接口（免费、稳定）

用法:
    python3 stock_cn.py 600936      # 查询上海股票
    python3 stock_cn.py 000001      # 查询深圳股票（自动识别）
    python3 stock_cn.py 600519 000858 000001  # 查询多只股票
"""

import urllib.request
import sys
import re


def get_stock_data(code):
    """获取单只股票数据"""
    code = str(code).strip()
    
    # 自动判断上海(sh)还是深圳(sz)
    # 上海：60xxxx, 68xxxx(科创), 50xxxx(指数)
    # 深圳：00xxxx, 30xxxx(创业), 20xxxx(创业)
    if code.startswith(('6', '5', '68', '51', '52', '56', '58', '59')):
        prefix = 'sh'
    else:
        prefix = 'sz'
    
    url = f'http://qt.gtimg.cn/q={prefix}{code}'
    
    try:
        response = urllib.request.urlopen(url, timeout=10)
        data = response.read().decode('gbk')
        
        match = re.search(rf'v_{prefix}{code}="(.*?)"', data)
        if match:
            fields = match.group(1).split('~')
            return {
                'name': fields[1],
                'code': fields[2],
                'price': float(fields[3]),
                'prev_close': float(fields[4]),
                'open': float(fields[5]),
                'change': float(fields[31]),
                'change_pct': float(fields[32]),
                'high': float(fields[33]),
                'low': float(fields[34]),
                'volume': int(fields[6]),  # 手
                'amount': float(fields[37]) / 10000,  # 万
                'time': fields[30],
            }
    except Exception as e:
        print(f"查询 {code} 出错: {e}")
    
    return None


def format_stock(data):
    """格式化输出股票信息"""
    if not data:
        return "查询失败"
    
    # 涨跌颜色符号
    change_symbol = "📈" if data['change'] >= 0 else "📉"
    change_sign = "+" if data['change'] >= 0 else ""
    
    lines = [
        f"",
        f"┌─────────────────────────────────┐",
        f"│ {data['name']:20} ({data['code']}) │",
        f"├─────────────────────────────────┤",
        f"│ 现价:     {data['price']:>8.2f} 元        │",
        f"│ 涨跌:     {change_sign}{data['change']:>7.2f} 元        │",
        f"│ 涨跌幅:   {change_symbol} {change_sign}{data['change_pct']:>6.2f}%       │",
        f"├─────────────────────────────────┤",
        f"│ 今开:     {data['open']:>8.2f}            │",
        f"│ 昨收:     {data['prev_close']:>8.2f}            │",
        f"│ 最高:     {data['high']:>8.2f}            │",
        f"│ 最低:     {data['low']:>8.2f}            │",
        f"├─────────────────────────────────┤",
        f"│ 成交量:   {data['volume']:>8,} 手      │",
        f"│ 成交额:   {data['amount']:>8.2f} 万      │",
        f"└─────────────────────────────────┘",
        f"更新时间: {data['time']}",
    ]
    
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n示例:")
        print("  python3 stock_cn.py 600936")
        print("  python3 stock_cn.py 600519 000858 000001")
        sys.exit(1)
    
    # 支持查询多只股票
    for code in sys.argv[1:]:
        data = get_stock_data(code)
        print(format_stock(data))


if __name__ == '__main__':
    main()
