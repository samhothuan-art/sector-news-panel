#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十大板块新闻监控 - Web版本
Flask应用，带可点击链接
"""

from flask import Flask, render_template, jsonify
import requests
import hashlib
from datetime import datetime

app = Flask(__name__)

# 十大板块关键词配置
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

IMPORTANT_EVENTS = ["业绩预增", "重大合同", "政策扶持", "中标", "订单", "涨价", 
                    "突破", "量产", "涨停", "暴涨", "暴跌", "利好", "利空"]

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
    
    def _is_important(self, title, content):
        return any(event in title + content for event in IMPORTANT_EVENTS)
    
    def _fix_url(self, url, source):
        """修复URL格式"""
        if not url:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        return url
    
    def fetch_all_news(self):
        all_news = []
        all_news.extend(self._fetch_sina())
        all_news.extend(self._fetch_eastmoney())
        all_news.extend(self._fetch_cls())
        all_news.extend(self._fetch_yicai())
        return all_news
    
    def _fetch_sina(self):
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
                        news_list.append({
                            'title': title,
                            'content': item.get('summary', ''),
                            'url': self._fix_url(item.get('url', ''), 'sina'),
                            'time': item.get('ctime', ''),
                            'source': '新浪财经',
                            'is_important': self._is_important(title, item.get('summary', ''))
                        })
        except Exception as e:
            print(f"新浪失败: {e}")
        return news_list
    
    def _fetch_eastmoney(self):
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
                        news_list.append({
                            'title': title,
                            'content': item.get('summary', ''),
                            'url': self._fix_url(item.get('url', ''), 'eastmoney'),
                            'time': item.get('showTime', ''),
                            'source': '东方财富',
                            'is_important': self._is_important(title, item.get('summary', ''))
                        })
        except Exception as e:
            print(f"东财失败: {e}")
        return news_list
    
    def _fetch_cls(self):
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
                            news_list.append({
                                'title': title,
                                'content': item.get('content', ''),
                                'url': self._fix_url(item.get('shareurl', ''), 'cls'),
                                'time': item.get('ctime', ''),
                                'source': '财联社',
                                'is_important': self._is_important(title, item.get('content', ''))
                            })
        except Exception as e:
            print(f"财联社失败: {e}")
        return news_list
    
    def _fetch_yicai(self):
        """抓取第一财经"""
        news_list = []
        try:
            url = "https://www.yicai.com/api/ajax/getlatest?page=1&pagesize=30"
            resp = self.session.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                news_data = data if isinstance(data, list) else data.get('data', [])
                for item in news_data:
                    if isinstance(item, dict):
                        title = item.get('NewsTitle', '')
                        if not self._is_duplicate(title):
                            news_list.append({
                                'title': title,
                                'content': item.get('NewsAbstract', ''),
                                'url': f"https://www.yicai.com/news/{item.get('NewsID', '')}",
                                'time': item.get('CreateDate', ''),
                                'source': '第一财经',
                                'is_important': self._is_important(title, item.get('NewsAbstract', ''))
                            })
        except Exception as e:
            print(f"第一财经失败: {e}")
        return news_list
    
    def classify_news(self, news_list):
        classified = {sector: [] for sector in SECTORS}
        for news in news_list:
            full_text = news['title'] + news.get('content', '')
            for sector, keywords in SECTORS.items():
                if any(kw in full_text for kw in keywords):
                    classified[sector].append(news)
                    break
        return classified

scraper = NewsScraper()

@app.route('/')
def index():
    """主页 - 展示新闻"""
    news_list = scraper.fetch_all_news()
    classified = scraper.classify_news(news_list)
    update_time = datetime.now().strftime('%m-%d %H:%M')
    return render_template('index.html', sectors=classified, update_time=update_time)

@app.route('/api/news')
def api_news():
    """API接口 - JSON格式"""
    news_list = scraper.fetch_all_news()
    classified = scraper.classify_news(news_list)
    return jsonify({
        'update_time': datetime.now().strftime('%m-%d %H:%M'),
        'data': classified
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
