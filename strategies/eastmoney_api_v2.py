#!/usr/bin/env python3
"""
东方财富API - 简化版（测试可用接口）
"""

import requests
import pandas as pd
from datetime import datetime

class EastMoneyAPI:
    """东方财富数据接口"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://quote.eastmoney.com/',
        })
    
    def get_stock_list(self):
        """获取股票列表（沪深A股）"""
        url = "http://81.push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': 1,
            'pz': 100,
            'po': 1,
            'np': 1,
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': 2,
            'invt': 2,
            'fid': 'f20',
            'fs': 'm:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23',
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f22,f23,f24,f25,f26,f27,f28,f29,f30,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87',
            '_': str(int(datetime.now().timestamp() * 1000))
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get('data') and data['data'].get('diff'):
                stocks = []
                for item in data['data']['diff']:
                    stocks.append({
                        'code': item.get('f12'),
                        'name': item.get('f14'),
                        'price': item.get('f2') / 100 if item.get('f2') else None,
                        'change_pct': item.get('f3') / 100 if item.get('f3') else None,
                        'change': item.get('f4') / 100 if item.get('f4') else None,
                        'volume': item.get('f5') / 10000 if item.get('f5') else None,  # 万手
                        'amount': item.get('f6') / 100000000 if item.get('f6') else None,  # 亿
                        'main_net': item.get('f20') / 10000 if item.get('f20') else None,  # 主力净流入（万）
                    })
                return pd.DataFrame(stocks)
        except Exception as e:
            print(f"错误: {e}")
        
        return None
    
    def get_eight_sectors(self):
        """获取八大板块资金流向"""
        # 板块对应的股票列表
        sector_stocks = {
            'AI算力': ['000977', '300308', '300502', '300394'],
            '半导体': ['688981', '002371', '603501', '600584'],
            '机器人': ['688017', '002472', '300124', '002050'],
            '新能源': ['300750', '002594', '601012', '300274'],
            '有色金属': ['600362', '601899', '600547', '000807'],
            '消费': ['600519', '000858', '601888', '300015'],
            '军工': ['600893', '002013', '000768', '002389'],
            '高股息': ['600900', '601088', '600036', '601728'],
        }
        
        # 先获取全市场数据
        df_all = self.get_stock_list()
        
        if df_all is None:
            return None
        
        # 按板块统计
        sector_data = []
        for sector, codes in sector_stocks.items():
            sector_df = df_all[df_all['code'].isin(codes)]
            
            if not sector_df.empty:
                avg_change = sector_df['change_pct'].mean()
                total_flow = sector_df['main_net'].sum()
                leader = sector_df.loc[sector_df['change_pct'].idxmax()]
                
                sector_data.append({
                    '板块': sector,
                    '平均涨跌': f"{avg_change:+.2f}%" if avg_change else '-',
                    '主力流入(万)': f"{total_flow:.0f}" if total_flow else '-',
                    '领涨股': leader['name'],
                    '领涨股涨跌': f"{leader['change_pct']:+.2f}%" if leader['change_pct'] else '-',
                })
        
        return pd.DataFrame(sector_data)

def test():
    """测试"""
    print("🚀 东方财富API测试")
    print(f"时间: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    api = EastMoneyAPI()
    
    # 获取八大板块数据
    print("获取八大板块资金流向...")
    df = api.get_eight_sectors()
    
    if df is not None and not df.empty:
        print("✅ 成功！")
        print()
        print(df.to_string(index=False))
    else:
        print("❌ 获取失败")

if __name__ == "__main__":
    test()
