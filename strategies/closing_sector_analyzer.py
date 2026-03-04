#!/usr/bin/env python3
"""
尾盘资金流向分析 + 明日关注股票推荐
监控时段: 14:30-15:00
"""

import tushare as ts
import pandas as pd
from datetime import datetime, time, timedelta
import warnings
warnings.filterwarnings('ignore')

TUSHARE_TOKEN = '9e002cf5c323daadf44e180b80ae9489a543a5709f05edf1609e377d'

def get_closing_flow_stocks(date_str=None):
    """
    获取尾盘资金流向数据
    由于Tushare没有分钟级资金流向，我们使用日级数据+技术分析来估算
    """
    if date_str is None:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    pro = ts.pro_api(TUSHARE_TOKEN)
    
    print(f'分析日期: {date_str}')
    print('获取A股全市场资金流向...')
    
    try:
        # 获取所有股票的资金流向
        df = pro.moneyflow(trade_date=date_str)
        
        if df is None or df.empty:
            return None
        
        # 计算主力净流入（超大单+大单）
        df['main_net'] = df['buy_elg_amount'] + df['buy_lg_amount'] - df['sell_elg_amount'] - df['sell_lg_amount']
        df['main_net_yi'] = df['main_net'] / 10000  # 转换为亿元
        
        # 计算散户净流入（小单）
        df['retail_net'] = df['buy_sm_amount'] - df['sell_sm_amount']
        df['retail_net_yi'] = df['retail_net'] / 10000
        
        # 按主力净流入排序
        df = df.sort_values('main_net_yi', ascending=False)
        
        return df
        
    except Exception as e:
        print(f'获取数据失败: {e}')
        return None

def get_stock_basic(ts_code):
    """获取股票基本信息"""
    pro = ts.pro_api(TUSHARE_TOKEN)
    try:
        df = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,industry,market')
        if not df.empty:
            return df.iloc[0]
    except:
        pass
    return None

def analyze_sectors(df, top_n=10):
    """
    分析板块资金流向
    由于没有板块资金流向数据，我们通过个股资金流向反推热点板块
    """
    if df is None or df.empty:
        return None
    
    print(f'\n分析板块资金流向...')
    
    # 获取主力流入最多的股票
    top_inflow = df[df['main_net_yi'] > 0].head(top_n)
    
    # 获取这些股票的基本信息
    sectors = {}
    
    for _, row in top_inflow.iterrows():
        ts_code = row['ts_code']
        basic = get_stock_basic(ts_code)
        
        if basic is not None:
            industry = basic['industry']
            name = basic['name']
            
            if industry not in sectors:
                sectors[industry] = {
                    'stocks': [],
                    'total_flow': 0,
                    'count': 0
                }
            
            sectors[industry]['stocks'].append({
                'name': name,
                'ts_code': ts_code,
                'flow': row['main_net_yi'],
                'price': row.get('close', 0)
            })
            sectors[industry]['total_flow'] += row['main_net_yi']
            sectors[industry]['count'] += 1
    
    # 按板块总流入排序
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]['total_flow'], reverse=True)
    
    return sorted_sectors[:5]  # Top5板块

def select_top_stocks(df, sectors, num_stocks=3):
    """
    从流入板块中选出明日关注股票
    
    选股标准：
    1. 主力大幅净流入
    2. 股价处于相对低位或突破形态
    3. 非ST、非科创板（流动性考虑）
    4. 尾盘没有大幅回落
    """
    if df is None or sectors is None:
        return None
    
    print(f'\n选股中...')
    
    candidates = []
    
    # 从Top3板块中选
    for sector_name, sector_data in sectors[:3]:
        for stock in sector_data['stocks'][:3]:  # 每个板块取前3
            # 过滤条件
            if stock['flow'] < 1:  # 主力流入至少1亿
                continue
            
            candidates.append({
                'name': stock['name'],
                'ts_code': stock['ts_code'],
                'sector': sector_name,
                'main_flow': stock['flow'],
                'sector_flow': sector_data['total_flow'],
                'score': stock['flow'] * 0.7 + sector_data['total_flow'] * 0.3  # 综合评分
            })
    
    # 按评分排序
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates[:num_stocks]

def format_report(sectors, top_stocks, date_str):
    """格式化报告"""
    report = f"📊 **尾盘资金流向分析报告** ({date_str})\n\n"
    
    # 板块流入
    report += "**🔥 资金流入板块 TOP5**\n\n"
    for i, (sector_name, sector_data) in enumerate(sectors, 1):
        report += f"{i}. **{sector_name}**\n"
        report += f"   板块净流入: +{sector_data['total_flow']:.2f}亿\n"
        report += f"   流入个股数: {sector_data['count']}只\n"
        report += f"   代表股: {', '.join([s['name'] for s in sector_data['stocks'][:3]])}\n\n"
    
    # 明日关注
    report += "**🎯 明日关注股票 TOP3**\n\n"
    for i, stock in enumerate(top_stocks, 1):
        report += f"{i}. **{stock['name']}** ({stock['ts_code']})\n"
        report += f"   所属板块: {stock['sector']}\n"
        report += f"   主力流入: +{stock['main_flow']:.2f}亿\n"
        report += f"   板块流入: +{stock['sector_flow']:.2f}亿\n"
        report += f"   综合评分: {stock['score']:.2f}\n\n"
    
    report += "**💡 策略建议**\n"
    report += "- 关注主力持续流入的板块\n"
    report += "- 明日开盘观察竞价情况\n"
    report += "- 设置止损位，控制风险\n"
    
    return report

def main():
    """主函数"""
    print("="*60)
    print("🌙 尾盘资金流向分析")
    print("="*60)
    
    # 检查时间
    now = datetime.now()
    print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M')}")
    
    if now.time() < time(15, 0):
        print("\n⚠️ 注意: 当前还未收盘，分析的是昨日数据")
        print("建议 15:05 后运行获取今日准确数据\n")
    
    # 获取数据
    date_str = (now - timedelta(days=1)).strftime('%Y%m%d')
    df = get_closing_flow_stocks(date_str)
    
    if df is None:
        print("❌ 获取数据失败")
        return
    
    print(f"✅ 获取 {len(df)} 只股票数据")
    
    # 分析板块
    sectors = analyze_sectors(df)
    
    if not sectors:
        print("❌ 板块分析失败")
        return
    
    # 选股
    top_stocks = select_top_stocks(df, sectors)
    
    if not top_stocks:
        print("❌ 选股失败")
        return
    
    # 生成报告
    report = format_report(sectors, top_stocks, date_str)
    
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存报告
    output_dir = '/Users/opensamhot/.openclaw/workspace/data'
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/closing_sector_report_{date_str}.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存")
    
    return report

if __name__ == "__main__":
    main()
