#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十大板块新闻监控脚本 - 飞书优化版
去重、智能摘要、带链接
"""

import requests
import hashlib
import sys
from datetime import datetime

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

# 重要事件关键词（触发摘要）
IMPORTANT_EVENTS = ["业绩预增", "重大合同", "政策扶持", "中标", "订单", "涨价", 
                    "突破", "量产", "涨停", "飙升", "暴涨", "暴跌", "利好", "利空",
                    "获批", "认证", "扩产", "并购", "收购", "重组"]

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.seen_hashes = set()  # 用于去重
    
    def _dedup_key(self, title):
        """生成去重key"""
        # 取标题前15个字符的hash
        key = title[:15].strip()
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_duplicate(self, title):
        """检查是否重复"""
        key = self._dedup_key(title)
        if key in self.seen_hashes:
            return True
        self.seen_hashes.add(key)
        return False
    
    def _is_important(self, title, content):
        """判断新闻是否重要"""
        full_text = title + content
        return any(event in full_text for event in IMPORTANT_EVENTS)
    
    def _generate_summary(self, title, content):
        """生成详细摘要"""
        full = title + "。" + content
        
        # 提取关键信息
        summary_parts = []
        
        # 股价/涨跌相关
        if "涨停" in full:
            summary_parts.append("股价涨停")
        elif "暴涨" in full or "大涨" in full:
            summary_parts.append("股价大涨")
        elif "跌停" in full:
            summary_parts.append("股价跌停")
        
        # 业绩相关
        if "业绩预增" in full or "净利润增长" in full:
            summary_parts.append("业绩预期向好")
        if "营收" in full and ("增长" in full or "增加" in full):
            summary_parts.append("营收增长")
        
        # 订单/合同
        if "重大合同" in full or "大单" in full:
            summary_parts.append("获得重大订单")
        if "中标" in full:
            summary_parts.append("中标重要项目")
        
        # 政策
        if "政策扶持" in full or "政策支持" in full:
            summary_parts.append("受政策利好支持")
        if "获批" in full or "通过审批" in full:
            summary_parts.append("项目/产品获批")
        
        # 价格
        if "涨价" in full:
            summary_parts.append("产品价格上涨")
        if "跌价" in full or "降价" in full:
            summary_parts.append("产品价格下降")
        
        # 技术/产能
        if "突破" in full:
            summary_parts.append("技术取得突破")
        if "量产" in full:
            summary_parts.append("进入量产阶段")
        if "扩产" in full or "产能扩张" in full:
            summary_parts.append("产能扩张")
        
        # 并购/合作
        if "并购" in full or "收购" in full:
            summary_parts.append("进行并购/收购")
        if "合作" in full:
            summary_parts.append("达成战略合作")
        
        # 市场/出海
        if "出海" in full or "出口" in full:
            summary_parts.append("海外市场拓展")
        if "订单爆满" in full or "供不应求" in full:
            summary_parts.append("市场需求旺盛")
        
        if summary_parts:
            return "；".join(summary_parts[:3])  # 最多3个要点
        
        # 如果没有触发关键词，返回内容前40字
        if len(content) > 20:
            return content[:40] + "..."
        return None
    
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
                        news_list.append({
                            'title': title,
                            'content': item.get('summary', ''),
                            'url': item.get('url', ''),
                            'source': 'sina'
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
                        news_list.append({
                            'title': title,
                            'content': item.get('summary', ''),
                            'url': item.get('url', ''),
                            'source': 'eastmoney'
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
                            news_list.append({
                                'title': title,
                                'content': item.get('content', ''),
                                'url': item.get('shareurl', ''),
                                'source': 'cls'
                            })
        except Exception as e:
            print(f"财联社失败: {e}", file=sys.stderr)
        return news_list
    
    def fetch_jin10_news(self):
        """抓取金十财经"""
        news_list = []
        try:
            url = "https://flash-api.jin10.com/get_flash_list"
            headers = {'Referer': 'https://www.jin10.com/'}
            params = {'channel': '-wv6wTtHtl', 'vip': '1'}
            resp = self.session.get(url, headers=headers, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('data', []):
                    content = item.get('content', '')
                    title = content[:50] + "..." if len(content) > 50 else content
                    if not self._is_duplicate(title):
                        news_list.append({
                            'title': title,
                            'content': content,
                            'url': item.get('link', ''),
                            'source': 'jin10'
                        })
        except Exception as e:
            print(f"金十失败: {e}", file=sys.stderr)
        return news_list
    
    def fetch_yicai_news(self):
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
                                'source': 'yicai'
                            })
        except Exception as e:
            print(f"第一财经失败: {e}", file=sys.stderr)
        return news_list
    
    def classify_news(self, news_list):
        """按板块分类"""
        classified = {sector: [] for sector in SECTORS}
        
        for news in news_list:
            full_text = news['title'] + news.get('content', '')
            
            # 判断重要性和生成摘要
            news['is_important'] = self._is_important(news['title'], news.get('content', ''))
            if news['is_important']:
                news['summary'] = self._generate_summary(news['title'], news.get('content', ''))
            else:
                news['summary'] = None
            
            # 分类到板块
            for sector, keywords in SECTORS.items():
                if any(kw in full_text for kw in keywords):
                    classified[sector].append(news)
                    break
        
        return classified
    
    def generate_report(self, classified_news):
        """生成报告 - 金十数据风格"""
        lines = []
        lines.append(f"📰 板块晨报 {datetime.now().strftime('%m-%d %H:%M')}")
        lines.append("")
        
        total = 0
        for sector, news_list in classified_news.items():
            if news_list:
                total += len(news_list)
                lines.append(f"━━━【{sector}】━━━")
                
                for news in news_list[:2]:  # 每板块最多2条
                    # 标题（重要标记）
                    if news.get('is_important'):
                        lines.append(f"🔴 {news['title']}")
                    else:
                        lines.append(f"• {news['title']}")
                    
                    # 正文摘要（一段话）
                    content = news.get('content', '')
                    if content:
                        summary = content[:70] + "..." if len(content) > 70 else content
                        lines.append(f"  {summary}")
                    
                    lines.append("")  # 空行分隔
        
        if total == 0:
            lines.append("📭 暂无相关板块重要新闻")
        
        return "\n".join(lines)

def main():
    scraper = NewsScraper()
    
    # 抓取所有来源
    all_news = []
    all_news.extend(scraper.fetch_sina_news())
    all_news.extend(scraper.fetch_eastmoney_news())
    all_news.extend(scraper.fetch_cls_news())
    all_news.extend(scraper.fetch_jin10_news())
    all_news.extend(scraper.fetch_yicai_news())
    
    # 分类并生成报告
    classified = scraper.classify_news(all_news)
    report = scraper.generate_report(classified)
    
    print(report)
    return report

if __name__ == "__main__":
    main()
