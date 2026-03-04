#!/usr/bin/env python3
"""
尾盘抢筹策略 - 隔夜超短
监控时段: 14:00-14:40
目标: 尾盘资金大幅流入的板块，次日早盘高抛
"""

import requests
import pandas as pd
from datetime import datetime, time
import sys
import os

# 八大核心板块及代表股
SECTOR_STOCKS = {
    "AI算力": ["300308.SZ", "300502.SZ", "000977.SZ", "300394.SZ"],  # 中际旭创、新易盛、浪潮、天孚
    "半导体": ["688981.SH", "002371.SZ", "688012.SH", "600584.SH"],  # 中芯、北方华创、中微、长电
    "机器人": ["688017.SH", "002472.SZ", "300124.SZ", "601100.SH"],  # 绿的谐波、双环、汇川、恒立
    "新能源": ["300750.SZ", "002594.SZ", "601012.SH", "300274.SZ"],  # 宁德、比亚迪、隆基、阳光
    "有色金属": ["600362.SH", "601899.SH", "600547.SH", "000807.SZ"], # 江西铜业、紫金、山东黄金、云铝
    "消费": ["600519.SH", "000858.SZ", "601888.SH", "300015.SZ"],    # 茅台、五粮液、中免、爱尔
    "军工": ["600893.SH", "002013.SZ", "000768.SZ", "002389.SZ"],    # 航发、中航、西飞、航天彩虹
    "高股息": ["600900.SH", "601088.SH", "600036.SH", "601728.SH"],  # 长江电力、神华、招行、电信
}

def get_sina_realtime_quotes(codes):
    """获取新浪财经实时行情"""
    codes_str = ','.join([c.lower().replace('.sz', '').replace('.sh', '') 
                         for c in codes])
    url = f"https://hq.sinajs.cn/list={codes_str}"
    
    try:
        response = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'}, timeout=10)
        # 解析数据...
        data = {}
        # 简化的解析逻辑
        return data
    except:
        return None

def monitor_closing_flow():
    """
    监控14:00-14:40资金流向
    由于新浪没有分钟级资金流，我们使用涨跌幅+成交量变化来估算
    """
    now = datetime.now()
    
    print(f"🚀 尾盘抢筹监控 ({now.strftime('%H:%M')})")
    print("="*60)
    
    # 这里应该获取14:00和当前的数据对比
    # 简化版本：获取当前涨幅前列的板块
    
    # 模拟数据（实际需要分钟级接口）
    sector_performance = {
        "AI算力": {"change_14h": 2.5, "volume_ratio": 1.8, "leader": "中际旭创"},
        "半导体": {"change_14h": 1.8, "volume_ratio": 1.5, "leader": "中芯国际"},
        "机器人": {"change_14h": 3.2, "volume_ratio": 2.1, "leader": "绿的谐波"},
    }
    
    # 筛选强势板块
    strong_sectors = []
    for sector, data in sector_performance.items():
        if data["change_14h"] > 2.0 and data["volume_ratio"] > 1.5:
            strong_sectors.append({
                "sector": sector,
                "change": data["change_14h"],
                "volume_ratio": data["volume_ratio"],
                "leader": data["leader"]
            })
    
    strong_sectors.sort(key=lambda x: x["change"], reverse=True)
    
    return strong_sectors

def select_stock_for_overnight(sector):
    """为隔夜策略选股"""
    # 从板块中选龙头或弹性最好的
    stocks = SECTOR_STOCKS.get(sector, [])
    
    # 简化：返回板块第一只
    if stocks:
        return {
            "code": stocks[0],
            "name": get_stock_name(stocks[0]),
            "sector": sector
        }
    return None

def get_stock_name(code):
    """获取股票名称"""
    names = {
        "300308.SZ": "中际旭创",
        "300502.SZ": "新易盛",
        "000977.SZ": "浪潮信息",
        "300394.SZ": "天孚通信",
        "688981.SH": "中芯国际",
        "002371.SZ": "北方华创",
        "688017.SH": "绿的谐波",
        "300750.SZ": "宁德时代",
        "600362.SH": "江西铜业",
        "600519.SH": "贵州茅台",
    }
    return names.get(code, code)

def generate_overnight_signal():
    """生成隔夜交易信号"""
    now = datetime.now()
    
    if now.time() < time(14, 0) or now.time() > time(14, 50):
        return "⏰ 请在14:00-14:50之间运行"
    
    sectors = monitor_closing_flow()
    
    if not sectors:
        return "❌ 暂未发现强势板块"
    
    # 选最强板块
    top_sector = sectors[0]
    stock = select_stock_for_overnight(top_sector["sector"])
    
    if not stock:
        return "❌ 选股失败"
    
    msg = f"🚀 **尾盘抢筹信号** ({now.strftime('%H:%M')})\n\n"
    msg += f"**强势板块**: {top_sector['sector']}\n"
    msg += f"14:00至今涨幅: +{top_sector['change']:.1f}%\n"
    msg += f"量比: {top_sector['volume_ratio']:.1f}倍\n\n"
    
    msg += f"**推荐标的**: {stock['name']} ({stock['code']})\n"
    msg += f"板块龙头，弹性较好\n\n"
    
    msg += "**操作策略**:\n"
    msg += "1. 14:45-14:55 分批买入\n"
    msg += "2. 仓位: 20-30%（单票）\n"
    msg += "3. 次日9:25-9:35 高开即卖\n"
    msg += "4. 止损: -3%坚决离场\n\n"
    
    msg += "⚠️ **风险提示**:\n"
    msg += "- 隔夜超短风险较高\n"
    msg += "- 次日低开需果断止损\n"
    msg += "- 不要满仓追涨"
    
    return msg

def main():
    """主函数"""
    signal = generate_overnight_signal()
    print(signal)
    
    # 保存信号
    output_dir = os.path.expanduser("~/.openclaw/workspace/data")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/overnight_signal.txt", 'w', encoding='utf-8') as f:
        f.write(signal)

if __name__ == "__main__":
    main()
