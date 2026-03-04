# 财经新闻API与开源项目汇总

> 用于搭建板块新闻监控系统

---

## 一、可用API接口

### 1. 新浪财经（推荐 ✅）

| 接口 | URL | 说明 |
|------|-----|------|
| **滚动新闻** | `https://feed.sina.com.cn/api/roll/get` | 实时财经新闻 |
| **个股新闻** | `https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php` | 个股相关新闻 |
| **行业板块** | `https://finance.sina.com.cn/stock/marketdata/` | 板块行情+新闻 |

**滚动新闻参数**:
```
pageid=153  &  # 页面ID
lid=2516     &  # 分类ID (2516=财经)
k=           &  # 关键词
num=10       &  # 数量
r=0.5            # 随机数防缓存
```

**板块分类ID**:
- 2516: 财经综合
- 2517: 股市
- 2518: 港股
- 2519: 美股
- 2520: 期货
- 其他需要测试

---

### 2. 东方财富（需要解析）

| 接口 | URL | 说明 |
|------|-----|------|
| **快讯** | `https://np-anotice-stock.eastmoney.com/api/security/ann` | 公告快讯 |
| **7x24** | `https://cmsapi.business.eastmoney.com/api/CmsApi/Trd_GetLiveText` | 7x24小时快讯 |

---

### 3. 财联社（专业但需授权）

| 接口 | URL | 说明 |
|------|-----|------|
| **电报** | `https://www.cls.cn/api/telegraph` | 实时财经电报 |

需要 `cls-token` 或其他认证参数

---

### 4. 聚合数据API（付费）

- **Juhe Data**: https://www.juhe.cn/docs/api/id/149
- **阿里云市场**: 有各种财经API套餐

---

## 二、GitHub开源项目

### 1. 新闻聚合类

| 项目 | 链接 | 特点 |
|------|------|------|
| **AKShare** | https://github.com/akfamily/akshare | 包含财经新闻接口 |
| **Tushare** | https://github.com/waditu/tushare | 包含新闻、公告数据 |
| **Efinance** | https://github.com/Micro-sheep/efinance | 东方财富数据获取 |

### 2. 财经爬虫类

| 项目 | 链接 | 特点 |
|------|------|------|
| **stock-crawler** | https://github.com/search?q=stock+news+crawler | 各种股票新闻爬虫 |
| **Crawler-For-Gov / 基金爬虫** | https://github.com/Smile-yang/funds | 基金新闻爬虫示例 |

### 3. NLP分析类

| 项目 | 链接 | 特点 |
|------|------|------|
| **FinNLP** | https://github.com/AI4Finance-Foundation/FinNLP | 金融NLP工具 |
| **Chinese-Financial-NLP** | https://github.com/search?q=chinese+financial+nlp | 中文金融NLP |

---

## 三、推荐方案

### 方案A：新浪API + 关键词过滤（简单）

```python
import requests
import json

def get_sina_news(keyword=None, num=20):
    \"\"\"获取新浪财经新闻\"\"\"
    url = 'https://feed.sina.com.cn/api/roll/get'
    params = {
        'pageid': 153,
        'lid': 2516,
        'k': keyword or '',
        'num': num,
        'r': 0.5
    }
    
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    news_list = []
    for item in data['result']['data']:
        news_list.append({
            'title': item['title'],
            'url': item['url'],
            'time': item['ctime'],
            'tag': item.get('tag', [])
        })
    
    return news_list

# 按板块关键词过滤
def filter_by_sector(news_list, keywords):
    \"\"\"筛选特定板块的新闻\"\"\"
    filtered = []
    for news in news_list:
        title = news['title']
        if any(kw in title for kw in keywords):
            filtered.append(news)
    return filtered

# 示例：半导体板块
keywords = ['半导体', '芯片', '集成电路', '光刻', '中芯', '北方华创']
news = get_sina_news()
sector_news = filter_by_sector(news, keywords)
```

---

### 方案B：AKShare + 多源聚合（推荐）

```python
import akshare as ak

# 获取财经新闻
df = ak.stock_news_em(stock="000001")  # 东方财富个股新闻
df = ak.stock_news_main_cx()           # 财联社电报
df = ak.stock_news_sina()              # 新浪财经

# 获取板块新闻
df = ak.stock_sector_news(symbol="半导体")
```

---

## 四、板块关键词库（示例）

等待用户补充完整板块列表

| 板块 | 关键词 |
|------|--------|
| 半导体 | 半导体、芯片、集成电路、光刻、中芯、北方华创、韦尔股份 |
| 新能源 | 新能源、光伏、锂电、宁德时代、比亚迪、储能 |
| AI算力 | AI、算力、服务器、浪潮、CPO、光模块、英伟达 |
| 机器人 | 机器人、减速器、特斯拉、人形机器人、宇树 |
| ... | ... |

---

## 五、实现步骤

1. **确定板块列表** ⬅️ 等待用户提供
2. **建立关键词库**
3. **定时获取新闻**（每30分钟/1小时）
4. **关键词过滤**
5. **生成简报推送**

---

*更新时间: 2026-02-25*
*状态: 等待板块列表*
