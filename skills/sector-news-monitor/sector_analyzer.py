#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十大板块情报与趋势判断助手
专业A股板块情报推送 - 早中晚3次
"""

import requests
import hashlib
import sys
import json
from datetime import datetime

# 十大核心板块配置
SECTORS = {
    "AI算力与应用": {
        "keywords": ["AI", "人工智能", "大模型", "光模块", "CPO", "液冷", "算力", "服务器", "数据中心", "智算中心"],
        "stocks": ["中际旭创", "新易盛", "浪潮信息", "工业富联", "科大讯飞"]
    },
    "半导体国产替代": {
        "keywords": ["半导体", "芯片", "光刻机", "光刻胶", "存储", "HBM", "先进封装", "国产替代", "中芯国际", "北方华创"],
        "stocks": ["北方华创", "中微公司", "兆易创新", "澜起科技", "长电科技"]
    },
    "人形机器人": {
        "keywords": ["人形机器人", "机器人", "减速器", "丝杠", "传感器", "Optimus", "宇树", "特斯拉机器人", "灵巧手"],
        "stocks": ["绿的谐波", "双环传动", "恒立液压", "贝斯特", "汇川技术"]
    },
    "有色金属/顺周期": {
        "keywords": ["铜", "铝", "黄金", "有色", "涨价", "稀土", "锂", "钴", "PPI", "顺周期", "江西铜业", "山东黄金"],
        "stocks": ["江西铜业", "云南铜业", "山东黄金", "赤峰黄金", "洛阳钼业"]
    },
    "新能源出海": {
        "keywords": ["新能源车", "锂电池", "光伏", "储能", "逆变器", "出海", "出口", "比亚迪", "宁德时代", "隆基"],
        "stocks": ["比亚迪", "宁德时代", "隆基绿能", "阳光电源", "晶科能源"]
    },
    "消费复苏": {
        "keywords": ["白酒", "免税", "旅游", "银发经济", "养老", "消费复苏", "茅台", "五粮液", "中国中免"],
        "stocks": ["贵州茅台", "五粮液", "中国中免", "宋城演艺", "爱尔眼科"]
    },
    "大军工": {
        "keywords": ["军工", "商业航天", "低空经济", "卫星", "无人机", "航天", "中航", "国防", "军品"],
        "stocks": ["中航西飞", "航天电器", "万丰奥威", "航天彩虹", "北斗星通"]
    },
    "高股息防御": {
        "keywords": ["高股息", "煤炭", "银行", "长江电力", "中国神华", "陕西煤业", "招商银行", "防御"],
        "stocks": ["中国神华", "陕西煤业", "长江电力", "招商银行", "中国移动"]
    },
    "工业母机": {
        "keywords": ["工业母机", "数控机床", "数控系统", "刀具", "精密加工", "机床", "海天精工", "秦川机床"],
        "stocks": ["海天精工", "秦川机床", "华中数控", "中钨高新", "科德数控"]
    },
    "电网电力": {
        "keywords": ["电力", "电网", "绿电", "Token出海", "新型电力系统", "储能", "虚拟电厂", "内蒙华电", "国电南瑞"],
        "stocks": ["内蒙华电", "国电南瑞", "长江电力", "三峡能源", "特变电工"]
    }
}

# 利好/利空关键词库
SENTIMENT_KEYWORDS = {
    "positive": {
        "业绩预增": 3, "净利润增长": 3, "扭亏为盈": 3, "大增": 2, "暴涨": 2, "涨停": 3,
        "重大合同": 3, "大单": 2, "中标": 2, "签约": 2, "战略合作": 2,
        "涨价": 2, "提价": 2, "产品涨价": 2,
        "突破": 2, "技术突破": 2, "量产": 2, "投产": 2, "扩产": 1, "产能释放": 1,
        "政策扶持": 2, "政策支持": 2, "补贴": 2, "获批": 2, "认证": 1, "许可证": 2,
        "资金流入": 1, "主力买入": 1, "机构增持": 2,
        "并购": 2, "收购": 2, "重组": 2, "资产注入": 2, "整体上市": 2,
        "出海": 1, "出口增长": 2, "海外订单": 2, "国际化": 1
    },
    "negative": {
        "业绩预减": 3, "净利润下降": 3, "亏损": 3, "暴雷": 3, "业绩变脸": 3, "不及预期": 2,
        "跌停": 3, "大跌": 2, "暴跌": 2, "崩盘": 3, "跳水": 2,
        "减持": 2, "大股东减持": 3, "套现": 2, "解禁": 2, "抛售": 2,
        "监管": 2, "问询函": 2, "关注函": 2, "立案调查": 3, "处罚": 2, "罚款": 1,
        "停产": 2, "停工": 2, "断供": 2, "订单取消": 2, "合同终止": 2,
        "降价": 2, "价格战": 2, "毛利率下降": 2, "成本上升": 1,
        "召回": 2, "质量问题": 2, "安全事故": 3, "环保问题": 2,
        "诉讼": 2, "仲裁": 2, "赔偿": 1
    }
}

class SectorNewsAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.seen_hashes = set()
    
    def _is_duplicate(self, title):
        key = hashlib.md5(title[:20].encode()).hexdigest()
        if key in self.seen_hashes:
            return True
        self.seen_hashes.add(key)
        return False
    
    def analyze_sentiment(self, title, content):
        """分析新闻情绪并返回评级"""
        full_text = title + content
        pos_score = sum(w for k, w in SENTIMENT_KEYWORDS["positive"].items() if k in full_text)
        neg_score = sum(w for k, w in SENTIMENT_KEYWORDS["negative"].items() if k in full_text)
        
        if pos_score >= 3 and pos_score > neg_score:
            return {"rating": "重大利好", "emoji": "📈🔥", "direction": "up"}
        elif pos_score > neg_score:
            return {"rating": "利好", "emoji": "📈", "direction": "up"}
        elif neg_score >= 3 and neg_score > pos_score:
            return {"rating": "重大利空", "emoji": "📉💔", "direction": "down"}
        elif neg_score > pos_score:
            return {"rating": "利空", "emoji": "📉", "direction": "down"}
        else:
            return {"rating": "中性", "emoji": "➡️", "direction": "neutral"}
    
    def fetch_news(self):
        """抓取多源新闻 - 优先移动端友好的来源"""
        all_news = []
        
        # 同花顺财经（可用API）
        try:
            url = "https://news.10jqka.com.cn/tapp/news/push/stock/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
            }
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == '200' or data.get('code') == 200:
                    for item in data.get('data', {}).get('list', [])[:25]:
                        title = item.get('title', '')
                        if not self._is_duplicate(title):
                            sent = self.analyze_sentiment(title, item.get('digest', ''))
                            # 使用移动端链接
                            url = item.get('appUrl', item.get('url', ''))
                            all_news.append({
                                'title': title,
                                'content': item.get('digest', ''),
                                'url': url,
                                'source': '同花顺',
                                'sentiment': sent
                            })
        except Exception as e:
            print(f"同花顺: {e}", file=sys.stderr)
        
        # 搜狐财经（备用）
        try:
            url = "https://v2.sohu.com/public-api/feed"
            params = {'scene': 'CATEGORY', 'sceneId': '1460', 'size': '15'}
            resp = self.session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('data', [])[:10]:
                    title = item.get('title', '')
                    if not self._is_duplicate(title):
                        sent = self.analyze_sentiment(title, '')
                        url = item.get('url', '')
                        if url:
                            all_news.append({
                                'title': title,
                                'content': '',
                                'url': url,
                                'source': '搜狐',
                                'sentiment': sent
                            })
        except Exception as e:
            print(f"搜狐: {e}", file=sys.stderr)
        
        return all_news
    
    def classify_by_sector(self, news_list):
        """按板块分类新闻"""
        classified = {sector: [] for sector in SECTORS}
        
        for news in news_list:
            full_text = news['title'] + news.get('content', '')
            matched = False
            
            for sector, data in SECTORS.items():
                keywords = data["keywords"]
                if any(kw in full_text for kw in keywords):
                    classified[sector].append(news)
                    matched = True
                    break
            
            # 如果没匹配到任何板块，检查是否涉及核心股票
            if not matched:
                for sector, data in SECTORS.items():
                    stocks = data["stocks"]
                    if any(stock in full_text for stock in stocks):
                        classified[sector].append(news)
                        break
        
        return classified
    
    def generate_sector_analysis(self, sector_name, news_list):
        """生成单个板块的分析"""
        if not news_list:
            return None
        
        # 统计情绪
        bullish = sum(1 for n in news_list if n['sentiment']['direction'] == 'up')
        bearish = sum(1 for n in news_list if n['sentiment']['direction'] == 'down')
        neutral = len(news_list) - bullish - bearish
        
        # 判断情绪强度
        if bullish >= 2 and bullish > bearish:
            emotion = "强" if bullish >= 3 else "偏强"
        elif bearish >= 2 and bearish > bullish:
            emotion = "弱" if bearish >= 3 else "偏弱"
        else:
            emotion = "中性"
        
        # 判断趋势
        major_news = [n for n in news_list if n['sentiment']['rating'] in ['重大利好', '重大利空']]
        if major_news:
            trend = "向上" if major_news[0]['sentiment']['direction'] == 'up' else "向下"
        elif bullish > bearish:
            trend = "向上"
        elif bearish > bullish:
            trend = "向下"
        else:
            trend = "震荡"
        
        # 核心逻辑（取最重要新闻）
        important = [n for n in news_list if '重大' in n['sentiment']['rating'] or n['sentiment']['rating'] in ['利好', '利空']]
        if important:
            logic = important[0]['title'][:40] + "..."
        else:
            logic = news_list[0]['title'][:40] + "..."
        
        return {
            'emotion': emotion,
            'trend': trend,
            'logic': logic,
            'news_count': len(news_list),
            'bullish': bullish,
            'bearish': bearish
        }
    
    def generate_trading_hint(self, sector_name, analysis):
        """生成交易提示"""
        if not analysis:
            return {"view": "观望", "catalyst": "暂无重要消息", "focus": "等待催化"}
        
        emotion = analysis['emotion']
        trend = analysis['trend']
        
        if emotion in ['强', '偏强'] and trend == '向上':
            view = "看多"
            catalyst = "利好因素占优，资金可能流入"
            focus = "关注龙头走势，逢低布局"
        elif emotion in ['弱', '偏弱'] and trend == '向下':
            view = "谨慎看空"
            catalyst = "利空因素主导，注意风险"
            focus = "减仓避险，等待企稳信号"
        elif trend == '震荡':
            view = "震荡观望"
            catalyst = "多空因素交织，方向不明"
            focus = "高抛低吸，控制仓位"
        else:
            view = "中性"
            catalyst = "消息平淡，跟随大盘"
            focus = "精选个股，不追热点"
        
        return {"view": view, "catalyst": catalyst, "focus": focus}
    
    def generate_report(self):
        """生成完整报告"""
        # 获取当前时间判断时段
        hour = datetime.now().hour
        if hour < 12:
            session = "早间"
        elif hour < 18:
            session = "午间"
        else:
            session = "晚间"
        
        lines = []
        lines.append(f"📊 **【{session}情报】十大板块趋势研判**")
        lines.append(f"⏰ {datetime.now().strftime('%m-%d %H:%M')} | 📰 共抓取新闻")
        lines.append("")
        
        # 抓取新闻
        news_list = self.fetch_news()
        classified = self.classify_by_sector(news_list)
        
        total_news = 0
        has_content_sectors = []
        
        for sector, sector_news in classified.items():
            if sector_news:
                total_news += len(sector_news)
                analysis = self.generate_sector_analysis(sector, sector_news)
                hint = self.generate_trading_hint(sector, analysis)
                has_content_sectors.append((sector, sector_news, analysis, hint))
        
        lines[1] = f"⏰ {datetime.now().strftime('%m-%d %H:%M')} | 📰 共{total_news}条"
        
        # 生成各板块报告
        for sector, sector_news, analysis, hint in has_content_sectors:
            lines.append(f"━━━━━━━━━━━━━━━")
            lines.append(f"**【{sector}】**")
            
            # 1. 新闻汇总（最多2条）
            for news in sector_news[:2]:
                sent = news['sentiment']
                title = news['title'][:35] + "..." if len(news['title']) > 35 else news['title']
                if news.get('url'):
                    lines.append(f"{sent['emoji']} [{title}]({news['url']}) *{sent['rating']}*")
                else:
                    lines.append(f"{sent['emoji']} {title} *{sent['rating']}*")
            
            # 2. 趋势判断
            lines.append(f"")
            lines.append(f"**趋势判断**:")
            lines.append(f"• 今日情绪: {analysis['emotion']}")
            lines.append(f"• 短期趋势: {analysis['trend']}")
            lines.append(f"• 核心逻辑: {analysis['logic']}")
            
            # 3. 操作提示
            lines.append(f"")
            lines.append(f"**操作提示**:")
            lines.append(f"• 观点: **{hint['view']}**")
            lines.append(f"• 关键催化/风险: {hint['catalyst']}")
            lines.append(f"• 关注重点: {hint['focus']}")
            lines.append("")
        
        if not has_content_sectors:
            lines.append("📭 暂无相关板块重要新闻")
        
        return "\n".join(lines)

def main():
    analyzer = SectorNewsAnalyzer()
    report = analyzer.generate_report()
    print(report)
    return report

if __name__ == "__main__":
    main()
