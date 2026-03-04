#!/usr/bin/env python3
"""
尾盘选股策略 - 基于板块资金流向挑选第二天胜率高的股票
"""

import json
import requests
import sys
from datetime import datetime

# 东方财富板块资金流向API
def get_sector_flow(top_n=10):
    """获取实时板块资金流向"""
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": top_n,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f62",  # 按主力净流入排序
        "fs": "m:90+t:2",  # 行业板块
        "fields": "f12,f14,f3,f62,f184,f20,f21,f267,f268,f269,f270",
        "_": int(datetime.now().timestamp() * 1000)
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        sectors = []
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff']:
                sector = {
                    'code': item.get('f12'),
                    'name': item.get('f14'),
                    'change_pct': item.get('f3', 0),
                    'main_inflow': item.get('f62', 0),  # 主力净流入（元）
                    'inflow_pct': item.get('f184', 0),  # 主力净流入占比
                    'total_cap': item.get('f20', 0),    # 总市值
                }
                sectors.append(sector)
        return sectors
    except Exception as e:
        print(f"Error fetching sector data: {e}")
        return []

# 获取板块内个股
def get_sector_stocks(sector_code, exclude_688=True, top_n=20):
    """获取板块内个股，排除688科创板"""
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 50,  # 多取一些，过滤后可能不够
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f62",
        "fs": f"b:{sector_code}",
        "fields": "f12,f14,f3,f5,f6,f20,f62,f184,f10,f21,f22,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f100,f102,f103,f104,f105,f106,f107,f108,f109,f110",
        "_": int(datetime.now().timestamp() * 1000)
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        stocks = []
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff']:
                code = item.get('f12', '')
                
                # 排除688科创板
                if exclude_688 and code.startswith('688'):
                    continue
                    
                # 排除ST/*ST
                name = item.get('f14', '')
                if 'ST' in name:
                    continue
                
                stock = {
                    'code': code,
                    'name': name,
                    'change_pct': item.get('f3', 0),
                    'volume': item.get('f5', 0),  # 成交量（手）
                    'amount': item.get('f6', 0),  # 成交额（元）
                    'main_inflow': item.get('f62', 0),  # 主力净流入
                    'inflow_pct': item.get('f184', 0),  # 主力净流入占比
                    'market_cap': item.get('f20', 0),   # 总市值
                    'turnover': item.get('f8', 0),      # 换手率
                    'pe': item.get('f9', 0),            # 市盈率
                    'pb': item.get('f23', 0),           # 市净率
                    'float_cap': item.get('f21', 0),    # 流通市值
                    'vol_ratio': item.get('f10', 0),    # 量比
                    'amp': item.get('f11', 0),          # 振幅
                }
                stocks.append(stock)
        
        return stocks[:top_n]
    except Exception as e:
        print(f"Error fetching stocks for sector {sector_code}: {e}")
        return []

# 尾盘选股评分
def score_stock(stock, market_phase='normal'):
    """
    尾盘选股评分 - 找第二天胜率高的
    考虑因素：
    1. 尾盘资金流入（主力净流入为正）
    2. 量价配合（放量上涨或缩量调整）
    3. 技术位置（非高位追涨）
    4. 盘子大小（适中最好）
    5. 换手率（活跃但不极端）
    """
    score = 0
    reasons = []
    
    change = stock.get('change_pct', 0)
    inflow = stock.get('main_inflow', 0)
    inflow_pct = stock.get('inflow_pct', 0)
    turnover = stock.get('turnover', 0)
    vol_ratio = stock.get('vol_ratio', 0)
    amp = stock.get('amp', 0)
    market_cap = stock.get('market_cap', 0)
    
    # 1. 主力净流入（核心）
    if inflow > 100000000:  # 1亿以上
        score += 30
        reasons.append("主力大幅流入")
    elif inflow > 50000000:  # 5000万以上
        score += 20
        reasons.append("主力明显流入")
    elif inflow > 0:
        score += 10
    
    if inflow_pct > 10:
        score += 15
        reasons.append("净流入占比>10%")
    elif inflow_pct > 5:
        score += 10
    
    # 2. 涨幅适中（不追高）
    if 2 <= change <= 6:  # 2-6%最佳
        score += 20
        reasons.append("涨幅适中")
    elif 0 < change < 2:  # 微涨蓄势
        score += 15
        reasons.append("温和上涨")
    elif change > 6:  # 追高扣分
        score -= 10
        reasons.append("涨幅过大，谨慎追高")
    
    # 3. 换手率（3-15%最佳）
    if 3 <= turnover <= 15:
        score += 15
        reasons.append("换手活跃")
    elif turnover > 20:  # 过高可能出货
        score -= 5
    
    # 4. 量比（1.5-5最佳）
    if 1.5 <= vol_ratio <= 5:
        score += 10
        reasons.append("放量明显")
    elif vol_ratio < 0.8:  # 缩量
        score -= 5
    
    # 5. 振幅（2-8%最佳）
    if 2 <= amp <= 8:
        score += 5
    
    # 6. 市值适中（50-500亿最佳）
    if 5000000000 <= market_cap <= 50000000000:
        score += 10
        reasons.append("盘子适中")
    elif market_cap < 3000000000:  # 小票波动大
        score += 5
    
    return score, reasons

# 主选股逻辑
def pick_stocks_from_sectors(sector_names=None, top_sectors=3, stocks_per_sector=2):
    """
    从热门板块中选股
    
    Args:
        sector_names: 指定的板块名称列表，None则自动选资金流向最强的
        top_sectors: 选前N个板块
        stocks_per_sector: 每个板块选N只股票
    """
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%H:%M')} 尾盘选股报告")
    print("=" * 60)
    
    # 获取板块资金流向
    sectors = get_sector_flow(top_n=15)
    if not sectors:
        print("❌ 获取板块数据失败")
        return
    
    print(f"\n📊 板块资金流向 TOP {top_sectors}：")
    print("-" * 60)
    
    target_sectors = []
    
    if sector_names:
        # 用户指定板块
        for name in sector_names:
            for s in sectors:
                if name in s['name']:
                    target_sectors.append(s)
                    break
    else:
        # 自动选最强的
        target_sectors = sectors[:top_sectors]
    
    for i, sector in enumerate(target_sectors, 1):
        inflow_yi = sector['main_inflow'] / 100000000  # 转亿元
        print(f"{i}. {sector['name']}: 涨{sector['change_pct']}% | 主力净流入{inflow_yi:.1f}亿 ({sector['inflow_pct']}%)")
    
    # 在每个板块内选股
    all_picks = []
    
    print(f"\n🎯 精选个股（排除688科创板）：")
    print("=" * 60)
    
    for sector in target_sectors:
        print(f"\n【{sector['name']}】")
        stocks = get_sector_stocks(sector['code'], exclude_688=True, top_n=30)
        
        if not stocks:
            print("  未获取到数据")
            continue
        
        # 评分排序
        scored = []
        for s in stocks:
            score, reasons = score_stock(s)
            if score > 30:  # 只显示有吸引力的
                scored.append((s, score, reasons))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        for s, score, reasons in scored[:stocks_per_sector]:
            cap_yi = s['market_cap'] / 100000000 if s['market_cap'] else 0
            print(f"  ⭐ {s['name']} ({s['code']})")
            print(f"     涨跌幅: {s['change_pct']}% | 主力净流入: {s['main_inflow']/10000:.0f}万")
            print(f"     换手率: {s['turnover']}% | 市值: {cap_yi:.0f}亿")
            print(f"     评分: {score}分 | 理由: {'; '.join(reasons)}")
            print()
            
            all_picks.append({
                'sector': sector['name'],
                **s,
                'score': score,
                'reasons': reasons
            })
    
    return all_picks

if __name__ == "__main__":
    # 命令行参数：可以指定板块名，如 "半导体 通信设备 电力"
    if len(sys.argv) > 1:
        sectors = sys.argv[1:]
        pick_stocks_from_sectors(sector_names=sectors)
    else:
        # 自动选资金流向最强的3个板块
        pick_stocks_from_sectors(top_sectors=3, stocks_per_sector=2)
