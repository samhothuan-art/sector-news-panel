#!/usr/bin/env python3
"""
尾盘抢筹实时监控
14:40运行，选出当日尾盘资金抢筹的板块和个股
次日早盘高开卖出
"""

import tushare as ts
import pandas as pd
from datetime import datetime, time, timedelta
import warnings
warnings.filterwarnings('ignore')

TUSHARE_TOKEN = '9e002cf5c323daadf44e180b80ae9489a543a5709f05edf1609e377d'

# 八大板块代表股
SECTOR_LEADERS = {
    "AI算力": ["000977.SZ", "300308.SZ", "300502.SZ", "300394.SZ"],  # 浪潮、中际、新易盛、天孚
    "半导体": ["688981.SH", "002371.SZ", "688012.SH", "603501.SH"],  # 中芯、北方、中微、韦尔
    "机器人": ["688017.SH", "002472.SZ", "300124.SZ", "002050.SZ"],  # 绿的、双环、汇川、三花
    "新能源": ["300750.SZ", "002594.SZ", "601012.SH", "300274.SZ"],  # 宁德、比亚迪、隆基、阳光
    "有色金属": ["600362.SH", "601899.SH", "600547.SH", "000807.SZ"], # 江西铜业、紫金、山东黄金、云铝
    "消费": ["600519.SH", "000858.SZ", "601888.SH", "300015.SZ"],    # 茅台、五粮液、中免、爱尔
    "军工": ["600893.SH", "002013.SZ", "000768.SZ", "002389.SZ"],    # 航发、中航、西飞、航天彩虹
    "高股息": ["600900.SH", "601088.SH", "600036.SH", "601728.SH"],  # 长江电力、神华、招行、电信
}

def get_today_performance():
    """获取今日各板块表现"""
    pro = ts.pro_api(TUSHARE_TOKEN)
    today = datetime.now().strftime('%Y%m%d')
    
    print(f"📊 获取今日行情 ({today})...")
    
    try:
        # 获取当日行情
        df = pro.daily(trade_date=today)
        
        if df is None or df.empty:
            # 如果今天没收盘，取昨天
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            df = pro.daily(trade_date=yesterday)
            print(f"使用昨日数据 ({yesterday})")
        
        return df
    except Exception as e:
        print(f"获取行情失败: {e}")
        return None

def analyze_sectors(df):
    """分析板块表现"""
    if df is None:
        return None
    
    sector_performance = []
    
    for sector, codes in SECTOR_LEADERS.items():
        sector_stocks = df[df['ts_code'].isin(codes)]
        
        if not sector_stocks.empty:
            avg_change = sector_stocks['pct_chg'].mean()
            avg_volume = sector_stocks['vol'].mean()
            leader = sector_stocks.loc[sector_stocks['pct_chg'].idxmax()]
            
            sector_performance.append({
                'sector': sector,
                'avg_change': avg_change,
                'leader_code': leader['ts_code'],
                'leader_name': get_stock_name(leader['ts_code']),
                'leader_change': leader['pct_chg'],
                'leader_volume': leader['vol'],
            })
    
    # 按涨幅排序
    sector_performance.sort(key=lambda x: x['avg_change'], reverse=True)
    
    return sector_performance

def get_stock_name(ts_code):
    """获取股票名称"""
    names = {
        '000977.SZ': '浪潮信息',
        '300308.SZ': '中际旭创',
        '300502.SZ': '新易盛',
        '300394.SZ': '天孚通信',
        '688981.SH': '中芯国际',
        '002371.SZ': '北方华创',
        '688012.SH': '中微公司',
        '603501.SH': '韦尔股份',
        '688017.SH': '绿的谐波',
        '002472.SZ': '双环传动',
        '300124.SZ': '汇川技术',
        '002050.SZ': '三花智控',
        '300750.SZ': '宁德时代',
        '002594.SZ': '比亚迪',
        '601012.SH': '隆基绿能',
        '300274.SZ': '阳光电源',
        '600362.SH': '江西铜业',
        '601899.SH': '紫金矿业',
        '600547.SH': '山东黄金',
        '600519.SH': '贵州茅台',
        '000858.SZ': '五粮液',
    }
    return names.get(ts_code, ts_code)

def generate_overnight_report(sector_data):
    """生成隔夜交易报告"""
    now = datetime.now()
    
    msg = f"🚀 **尾盘抢筹策略报告** ({now.strftime('%H:%M')})\n"
    msg += f"📅 {now.strftime('%Y-%m-%d')}\n\n"
    
    # 板块排名
    msg += "**📊 八大板块今日表现**\n\n"
    for i, s in enumerate(sector_data[:5], 1):
        emoji = "🔴" if s['avg_change'] > 0 else "🟢"
        msg += f"{i}. {emoji} **{s['sector']}**\n"
        msg += f"   板块平均: {s['avg_change']:+.2f}%\n"
        msg += f"   龙头: {s['leader_name']} ({s['leader_change']:+.2f}%)\n\n"
    
    # 选出最强板块
    top_sector = sector_data[0]
    
    # 选出1-2只标的
    msg += "**🎯 尾盘抢筹标的**\n\n"
    
    # 选板块内最强的1-2只
    candidates = [s for s in sector_data if s['sector'] == top_sector['sector']]
    
    msg += f"强势板块: **{top_sector['sector']}**\n"
    msg += f"龙头: {top_sector['leader_name']} ({top_sector['leader_code']})\n"
    msg += f"今日涨幅: {top_sector['leader_change']:+.2f}%\n\n"
    
    msg += "**📋 操作策略**\n"
    msg += "1. 买入时间: 14:45-14:55\n"
    msg += "2. 买入仓位: 单票20-30%，总仓位≤70%\n"
    msg += "3. 次日卖出: 9:25-9:35高开即卖\n"
    msg += "4. 止损位: 买入价-3%\n\n"
    
    msg += "**⚠️ 风险提示**\n"
    msg += "• 隔夜超短策略，风险较高\n"
    msg += "• 次日低开必须果断止损\n"
    msg += "• 不要满仓，留有余地\n"
    
    return msg

def main():
    """主函数"""
    print("="*60)
    print("🚀 尾盘抢筹策略")
    print("="*60)
    print()
    
    # 获取今日行情
    df = get_today_performance()
    
    if df is None:
        print("❌ 获取数据失败")
        return
    
    print(f"✅ 获取 {len(df)} 只股票数据\n")
    
    # 分析板块
    sector_data = analyze_sectors(df)
    
    if not sector_data:
        print("❌ 板块分析失败")
        return
    
    # 生成报告
    report = generate_overnight_report(sector_data)
    
    print(report)
    print("="*60)
    
    # 保存
    import os
    output_dir = '/Users/opensamhot/.openclaw/workspace/data'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/overnight_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n✅ 报告已保存")

if __name__ == "__main__":
    main()
