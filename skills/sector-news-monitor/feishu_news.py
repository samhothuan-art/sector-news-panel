#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十大板块新闻监控 - 智能情绪分析版
分析每条新闻是利好还是利空，预测板块影响方向
"""

import requests
import hashlib
import sys
from datetime import datetime

# 十大板块配置
SECTORS = {
    "AI算力": ["AI", "人工智能", "大模型", "光模块", "CPO", "液冷", "算力", "服务器"],
    "半导体": ["半导体", "芯片", "光刻机", "光刻胶", "存储", "HBM", "先进封装", "国产替代"],
    "人形机器人": ["人形机器人", "机器人", "减速器", "丝杠", "传感器", "Optimus", "宇树"],
    "有色金属": ["铜", "铝", "黄金", "有色", "涨价", "稀土", "锂", "钴", "锂矿"],
    "新能源": ["新能源车", "锂电池", "光伏", "储能", "逆变器", "比亚迪", "宁德时代"],
    "消费": ["白酒", "免税", "旅游", "银发经济", "养老", "消费复苏", "茅台"],
    "军工": ["军工", "商业航天", "低空经济", "卫星", "无人机", "航天"],
    "高股息": ["高股息", "煤炭", "银行", "长江电力", "中国神华"],
    "工业母机": ["工业母机", "数控机床", "数控系统", "刀具"],
    "电网电力": ["电力", "电网", "绿电", "Token出海", "虚拟电厂", "内蒙华电"]
}

# 利好关键词
POSITIVE_KEYWORDS = {
    "业绩预增": 3, "净利润增长": 3, "扭亏为盈": 3, "大增": 2, "暴涨": 2,
    "重大合同": 3, "大单": 2, "中标": 2, "签约": 2, "战略合作": 2,
    "涨价": 2, "提价": 2, "产品涨价": 2,
    "突破": 2, "技术突破": 2, "量产": 2, "投产": 2, "扩产": 1,
    "政策扶持": 2, "政策支持": 2, "补贴": 2, "获批": 2, "认证": 1,
    "涨停": 3, "大涨": 2, "飙升": 2, "创新高": 2, "资金流入": 1,
    "并购": 2, "收购": 2, "重组": 2, "资产注入": 2,
    "出海": 1, "出口增长": 2, "海外订单": 2
}

# 利空关键词
NEGATIVE_KEYWORDS = {
    "业绩预减": 3, "净利润下降": 3, "亏损": 3, "暴雷": 3, "业绩变脸": 3,
    "跌停": 3, "大跌": 2, "暴跌": 2, "崩盘": 3, "跳水": 2,
    "减持": 2, "大股东减持": 3, "套现": 2, "解禁": 2,
    "监管": 2, "问询函": 2, "关注函": 2, "立案调查": 3, "处罚": 2,
    "停产": 2, "停工": 2, "断供": 2, "订单取消": 2,
    "降价": 2, "价格战": 2, "毛利率下降": 2, "成本上升": 1,
    "召回": 2, "质量问题": 2, "安全事故": 3, "诉讼": 2
}

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.seen_hashes = set()
    
    def _is_duplicate(self, title):
        key = hashlib.md5(title[:15].encode()).hexdigest()
        if key in self.seen_hashes:
            return True
        self.seen_hashes.add(key)
        return False
    
    def analyze_sentiment(self, title, content):
        """分析新闻情绪：利好/利空/中性"""
        full_text = title + content
        
        positive_score = 0
        negative_score = 0
        
        for keyword, weight in POSITIVE_KEYWORDS.items():
            if keyword in full_text:
                positive_score += weight
        
        for keyword, weight in NEGATIVE_KEYWORDS.items():
            if keyword in full_text:
                negative_score += weight
        
        if positive_score > negative_score:
            if positive_score >= 3:
                return {"emoji": "📈🔥", "text": "重大利好", "score": positive_score}
            elif positive_score >= 2:
                return {"emoji": "📈", "text": "利好", "score": positive_score}
            else:
                return {"emoji": "📈", "text": "偏利好", "score": positive_score}
        elif negative_score > positive_score:
            if negative_score >= 3:
                return {"emoji": "📉💔", "text": "重大利空", "score": negative_score}
            elif negative_score >= 2:
                return {"emoji": "📉", "text": "利空", "score": negative_score}
            else:
                return {"emoji": "📉", "text": "偏利空", "score": negative_score}
        else:
            return {"emoji": "➡️", "text": "中性", "score": 0}
    
    def fetch_sina_news(self):
        """抓取新浪财经"""
        news_list = []
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get"
            params = {'pageid': '153', 'lid': '2509', 'num': '50', 'page': '1'}
            resp = self.session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('result', {}).get('data', []):
                    title = item.get('title', '')
                    if not self._is_duplicate(title):
                        sentiment = self.analyze_sentiment(title, item.get('summary', ''))
                        news_list.append({
                            'title': title,
                            'content': item.get('summary', ''),
                            'url': item.get('url', ''),
                            'source': '新浪',
                            'sentiment': sentiment
                        })
        except Exception as e:
            print(f"新浪失败: {e}", file=sys.stderr)
        return news_list
    
    def fetch_eastmoney_news(self):
        """抓取东方财富"""
        news_list = []
        try:
            url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102"
            params = {'client': 'wap', 'type': '1', 'pageSize': '50'}
            resp = self.session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('data', {}).get('fastNewsList', []):
                    title = item.get('title', '')
                    if not self._is_duplicate(title):
                        sentiment = self.analyze_sentiment(title, item.get('summary', ''))
                        news_list.append({
                            'title': title,
                            'content': item.get('summary', ''),
                            'url': item.get('url', ''),
                            'source': '东财',
                            'sentiment': sentiment
                        })
        except Exception as e:
            print(f"东财失败: {e}", file=sys.stderr)
        return news_list
    
    def fetch_cls_news(self):
        """抓取财联社"""
        news_list = []
        try:
            url = "https://www.cls.cn/api/telegraph"
            params = {'app': 'CailianpressWeb', 'os': 'web', 'sv': '8.4.6'}
            resp = self.session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 200:
                    for item in data.get('data', {}).get('roll_data', []):
                        title = item.get('title', '')
                        if not self._is_duplicate(title):
                            sentiment = self.analyze_sentiment(title, item.get('content', ''))
                            news_list.append({
                                'title': title,
                                'content': item.get('content', ''),
                                'url': item.get('shareurl', ''),
                                'source': '财联社',
                                'sentiment': sentiment
                            })
        except Exception as e:
            print(f"财联社失败: {e}", file=sys.stderr)
        return news_list
    
    def classify_news(self, news_list):
        """按板块分类"""
        classified = {sector: [] for sector in SECTORS}
        for news in news_list:
            full_text = news['title'] + news.get('content', '')
            for sector, keywords in SECTORS.items():
                if any(kw in full_text for kw in keywords):
                    classified[sector].append(news)
                    break
        return classified
    
    def generate_report(self, classified_news):
        """生成飞书消息"""
        lines = []
        lines.append(f"📰 **十大板块晨报** | {datetime.now().strftime('%m-%d')}")
        lines.append("💡 *新闻情绪分析：📈利好 📉利空 ➡️中性*")
        
        total = 0
        for sector, news_list in classified_news.items():
            if news_list:
                total += len(news_list)
                lines.append(f"\n**【{sector}】** ({len(news_list)}条)")
                
                for news in news_list[:2]:
                    sent = news.get('sentiment', {})
                    emoji = sent.get('emoji', '➡️')
                    level = sent.get('text', '中性')
                    
                    title = news['title'][:38] + "..." if len(news['title']) > 38 else news['title']
                    url = news.get('url', '')
                    
                    # 格式: [情绪] 标题 (影响)
                    if url:
                        lines.append(f"{emoji} [{title}]({url}) *{level}*")
                    else:
                        lines.append(f"{emoji} {title} *{level}*")
        
        if total == 0:
            lines.append("\n📭 暂无相关板块重要新闻")
        else:
            lines.append(f"\n📊 共 **{total}** 条相关新闻")
            bullish = sum(1 for sector in classified_news.values() for n in sector if n.get('sentiment', {}).get('emoji', '').startswith('📈'))
            bearish = sum(1 for sector in classified_news.values() for n in sector if n.get('sentiment', {}).get('emoji', '').startswith('📉'))
            lines.append(f"📈 利好: {bullish}条 | 📉 利空: {bearish}条")
        
        return "\n".join(lines)

def main():
    scraper = NewsScraper()
    
    print("正在抓取新闻...", file=sys.stderr)
    all_news = []
    all_news.extend(scraper.fetch_sina_news())
    all_news.extend(scraper.fetch_eastmoney_news())
    all_news.extend(scraper.fetch_cls_news())
    
    print("正在分类分析...", file=sys.stderr)
    classified = scraper.classify_news(all_news)
    report = scraper.generate_report(classified)
    
    print(report)
    return report

if __name__ == "__main__":
    main()
