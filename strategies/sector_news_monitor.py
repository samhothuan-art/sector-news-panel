#!/usr/bin/env python3
"""
2026主线板块新闻监控
监控2026年五大主线板块的实时新闻
"""

import requests
import pandas as pd
from datetime import datetime
import time
import json
import os

# ============ 板块关键词配置 ============

SECTOR_KEYWORDS = {
    "AI算力": {
        "keywords": ["AI", "人工智能", "大模型", "算力", "光模块", "CPO", "液冷", "服务器", "智算中心"],
        "priority": "P0",
        "color": "🔴"
    },
    "半导体": {
        "keywords": ["半导体", "芯片", "光刻机", "光刻胶", "存储", "HBM", "先进封装", "国产替代", "中芯"],
        "priority": "P0",
        "color": "🔴"
    },
    "人形机器人": {
        "keywords": ["人形机器人", "机器人", "减速器", "丝杠", "传感器", "Optimus", "宇树", "特斯拉"],
        "priority": "P0",
        "color": "🔴"
    },
    "新能源出海": {
        "keywords": ["新能源车", "锂电池", "光伏", "储能", "逆变器", "出海", "比亚迪", "宁德时代"],
        "priority": "P1",
        "color": "🟠"
    },
    "顺周期": {
        "keywords": ["铜", "铝", "黄金", "有色", "涨价", "化工", "MDI", "煤炭", "石油"],
        "priority": "P1",
        "color": "🟠"
    },
    "消费复苏": {
        "keywords": ["白酒", "医药", "旅游", "免税", "银发经济", "养老", "医疗服务"],
        "priority": "P2",
        "color": "🟡"
    },
    "高股息": {
        "keywords": ["电力", "水电", "煤炭", "银行", "保险", "高股息", "分红"],
        "priority": "P2",
        "color": "🟢"
    }
}

# ============ 新闻获取 ============

def get_sina_news(num=50):
    """获取新浪财经滚动新闻"""
    url = f'https://feed.sina.com.cn/api/roll/get?pageid=153&lid=2516&num={num}&r=0.5'
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = response.json()
        
        # 检查数据结构
        if 'result' not in data or 'data' not in data['result']:
            print(f"API返回异常: {list(data.keys())}")
            return []
        
        news_list = []
        for item in data['result']['data']:
            if 'title' in item:
                news_list.append({
                    'title': item['title'],
                    'url': item.get('url', ''),
                    'time': item.get('ctime', ''),
                    'tags': item.get('tags', [])
                })
        
        return news_list
    except Exception as e:
        print(f"获取新闻失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def classify_news(news_list):
    """按板块分类新闻"""
    sector_news = {sector: [] for sector in SECTOR_KEYWORDS}
    
    for news in news_list:
        title = news['title']
        matched = False
        
        for sector, config in SECTOR_KEYWORDS.items():
            keywords = config['keywords']
            if any(kw in title for kw in keywords):
                sector_news[sector].append(news)
                matched = True
                break
        
        if not matched:
            # 未分类
            if 'other' not in sector_news:
                sector_news['other'] = []
            sector_news['other'].append(news)
    
    return sector_news

# ============ 生成简报 ============

def generate_report(sector_news):
    """生成板块新闻简报"""
    report = f"📰 **主线板块新闻简报** ({datetime.now().strftime('%H:%M')})\n\n"
    
    # 按优先级排序
    priority_order = ['P0', 'P1', 'P2']
    
    for priority in priority_order:
        priority_sectors = [
            (s, c) for s, c in SECTOR_KEYWORDS.items() 
            if c['priority'] == priority and sector_news.get(s)
        ]
        
        if priority_sectors:
            report += f"**{'='*40}**\n"
            report += f"**{priority}级板块**\n\n"
            
            for sector, config in priority_sectors:
                news_list = sector_news[sector]
                color = config['color']
                
                report += f"{color} **{sector}** ({len(news_list)}条)\n\n"
                
                for i, news in enumerate(news_list[:5], 1):  # 每个板块最多5条
                    report += f"{i}. {news['title']}\n"
                    # report += f"   {news['url']}\n"  # URL太长，暂时隐藏
                
                report += "\n"
    
    # 统计
    total_classified = sum(len(v) for k, v in sector_news.items() if k != 'other')
    total_other = len(sector_news.get('other', []))
    
    report += f"**📊 统计**\n"
    report += f"- 主线板块新闻: {total_classified}条\n"
    report += f"- 其他新闻: {total_other}条\n"
    
    return report

def save_report(report):
    """保存报告到文件"""
    output_dir = os.path.expanduser("~/.openclaw/workspace/data/news_reports")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_path = os.path.join(output_dir, f"sector_news_{timestamp}.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return file_path

# ============ 主程序 ============

def main():
    """主函数"""
    print("="*60)
    print("📰 2026主线板块新闻监控")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    # 获取新闻
    print("获取新浪财经新闻...")
    news_list = get_sina_news(num=50)
    print(f"✅ 获取 {len(news_list)} 条新闻")
    print()
    
    if not news_list:
        print("❌ 未获取到新闻")
        return
    
    # 分类
    print("按板块分类...")
    sector_news = classify_news(news_list)
    print("✅ 分类完成")
    print()
    
    # 显示统计
    print("板块新闻统计:")
    for sector, news in sector_news.items():
        if sector != 'other' and news:
            config = SECTOR_KEYWORDS.get(sector, {})
            color = config.get('color', '⚪')
            priority = config.get('priority', 'P?')
            print(f"  {color} {sector} ({priority}): {len(news)}条")
    print()
    
    # 生成报告
    report = generate_report(sector_news)
    
    # 显示报告
    print("="*60)
    print(report)
    print("="*60)
    
    # 保存
    file_path = save_report(report)
    print(f"\n✅ 报告已保存: {file_path}")
    
    return report

if __name__ == "__main__":
    main()
