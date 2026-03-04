#!/usr/bin/env python3
"""
东方财富API实时数据获取
支持：实时行情、资金流向、板块排行
"""

import requests
import pandas as pd
import json
from datetime import datetime

class EastMoneyAPI:
    """东方财富API封装"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_realtime_quotes(self, codes):
        """
        获取实时行情
        codes: list of ['600519.SH', '000001.SZ']
        """
        # 转换代码格式
        code_list = []
        for code in codes:
            if '.SH' in code:
                code_list.append(f"1.{code.replace('.SH', '')}")
            elif '.SZ' in code:
                code_list.append(f"0.{code.replace('.SZ', '')}")
        
        url = f"http://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {
            'fltt': 2,
            'invt': 2,
            'fields': 'f12,f13,f14,f20,f21,f23,f24,f25,f26,f27,f28,f29,f30,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87',
            'secids': ','.join(code_list)
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and 'diff' in data['data']:
                stocks = []
                for item in data['data']['diff'].values():
                    stocks.append({
                        'code': item.get('f12'),
                        'name': item.get('f14'),
                        'price': item.get('f2') / 100 if item.get('f2') else 0,  # 当前价
                        'change_pct': item.get('f3') / 100 if item.get('f3') else 0,  # 涨跌幅
                        'volume': item.get('f5'),  # 成交量
                        'amount': item.get('f6') / 10000 if item.get('f6') else 0,  # 成交额（万）
                        'main_net': item.get('f20') / 10000 if item.get('f20') else 0,  # 主力净流入（万）
                    })
                return pd.DataFrame(stocks)
            return None
        except Exception as e:
            print(f"获取行情失败: {e}")
            return None
    
    def get_sector_fund_flow(self, sector_code='90.BK0477'):
        """
        获取板块资金流向
        sector_code: 板块代码
        """
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': 1,
            'pz': 50,
            'po': 1,
            'np': 1,
            'fltt': 2,
            'invt': 2,
            'fid': 'f20',  # 按主力净流入排序
            'fs': sector_code,  # 板块代码
            'fields': 'f12,f14,f20,f21,f22,f23,f24,f25,f26,f27',
            '_': int(datetime.now().timestamp() * 1000)
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and 'diff' in data['data']:
                stocks = []
                for item in data['data']['diff']:
                    stocks.append({
                        'code': item.get('f12'),
                        'name': item.get('f14'),
                        'main_net': item.get('f20') / 10000 if item.get('f20') else 0,  # 主力净流入
                        'main_net_pct': item.get('f21') / 100 if item.get('f21') else 0,  # 主力净流入占比
                    })
                return pd.DataFrame(stocks)
            return None
        except Exception as e:
            print(f"获取板块数据失败: {e}")
            return None
    
    def get_all_sectors_fund_flow(self):
        """获取所有板块资金流向排名"""
        # 主要板块代码
        sectors = {
            '有色金属': '90.BK0478',
            '半导体': '90.BK0539',
            '人工智能': '90.BK0559',
            '新能源': '90.BK0493',
            '军工': '90.BK0490',
            '白酒': '90.BK0896',
        }
        
        result = []
        for name, code in sectors.items():
            df = self.get_sector_fund_flow(code)
            if df is not None and not df.empty:
                total_flow = df['main_net'].sum()
                result.append({
                    'sector': name,
                    'code': code,
                    'total_flow': total_flow,
                    'top_stock': df.iloc[0]['name'] if len(df) > 0 else ''
                })
        
        return pd.DataFrame(result).sort_values('total_flow', ascending=False)

def test_api():
    """测试API"""
    print("🚀 东方财富API测试")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    api = EastMoneyAPI()
    
    # 测试1：获取个股实时行情
    print("1️⃣ 测试实时行情...")
    codes = ['000977.SZ', '601138.SH', '002171.SZ', '300308.SZ']
    df = api.get_realtime_quotes(codes)
    
    if df is not None and not df.empty:
        print("✅ 成功获取行情数据")
        print(df[['code', 'name', 'price', 'change_pct', 'main_net']].to_string())
    else:
        print("❌ 获取失败")
    
    print()
    
    # 测试2：获取板块资金流向
    print("2️⃣ 测试板块资金流向...")
    df_sectors = api.get_all_sectors_fund_flow()
    
    if df_sectors is not None and not df_sectors.empty:
        print("✅ 成功获取板块数据")
        print(df_sectors.to_string())
    else:
        print("❌ 获取失败")

if __name__ == "__main__":
    test_api()
