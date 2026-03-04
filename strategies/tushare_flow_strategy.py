#!/usr/bin/env python3
"""
尾盘资金流向策略 - Tushare Pro 版本
使用官方数据源，更准确可靠

Tushare Pro 资金流向说明：
- moneyflow 接口提供日级资金流向数据
- 单位：万元
- 字段说明：
  - buy_sm_amount: 小单买入金额（万元）
  - sell_sm_amount: 小单卖出金额（万元）
  - buy_md_amount: 中单买入金额（万元）
  - sell_md_amount: 中单卖出金额（万元）
  - buy_lg_amount: 大单买入金额（万元）
  - sell_lg_amount: 大单卖出金额（万元）
  - buy_elg_amount: 特大单买入金额（万元）
  - sell_elg_amount: 特大单卖出金额（万元）
  - net_mf_amount: 净流入金额（万元）
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Tushare Pro Token
TUSHARE_TOKEN = '9e002cf5c323daadf44e180b80ae9489a543a5709f05edf1609e377d'

class TushareFlowStrategy:
    """
    基于 Tushare Pro 的资金流向策略
    """
    
    def __init__(self, stock_code: str, stock_name: str, market: str = 'SZ'):
        """
        Args:
            stock_code: 股票代码，如 "000001"
            stock_name: 股票名称
            market: 市场，SZ/SH
        """
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.market = market
        self.ts_code = f"{stock_code}.{market}"
        self.pro = ts.pro_api(TUSHARE_TOKEN)
    
    def get_moneyflow(self, days: int = 5):
        """
        获取最近资金流向数据
        
        Returns:
            DataFrame with moneyflow data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days*2)  # 多取一些，避免周末假期
        
        try:
            df = self.pro.moneyflow(
                ts_code=self.ts_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )
            
            if df is None or df.empty:
                return None
            
            df = df.sort_values('trade_date')
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            # 转换为亿元
            for col in ['buy_sm_amount', 'sell_sm_amount', 'buy_md_amount', 'sell_md_amount',
                       'buy_lg_amount', 'sell_lg_amount', 'buy_elg_amount', 'sell_elg_amount',
                       'net_mf_amount']:
                df[f'{col}_yi'] = df[col] / 10000
            
            return df
            
        except Exception as e:
            print(f"获取{self.stock_name}资金流向失败: {e}")
            return None
    
    def analyze(self):
        """
        分析资金流向并生成交易信号
        
        Returns:
            dict: 分析结果
        """
        df = self.get_moneyflow(days=10)
        
        if df is None or df.empty:
            return None
        
        # 获取最新一天的数据
        latest = df.iloc[-1]
        
        # 计算主力净流入（大单+特大单）
        main_in = latest['buy_lg_amount_yi'] + latest['buy_elg_amount_yi']
        main_out = latest['sell_lg_amount_yi'] + latest['sell_elg_amount_yi']
        main_net = main_in - main_out
        
        # 计算散户净流入（小单）
        retail_in = latest['buy_sm_amount_yi']
        retail_out = latest['sell_sm_amount_yi']
        retail_net = retail_in - retail_out
        
        # 获取前几日数据用于趋势判断
        if len(df) >= 3:
            recent_3d = df.tail(3)['net_mf_amount_yi'].sum()
            trend = '连续流入' if recent_3d > 0 else '连续流出'
        else:
            recent_3d = latest['net_mf_amount_yi']
            trend = '数据不足'
        
        # 生成交易信号
        if main_net > 1 and latest['net_mf_amount_yi'] > 0:
            signal = 'BUY'
            confidence = 'HIGH'
            reason = '主力大幅净流入，态度积极'
        elif main_net > 0 and latest['net_mf_amount_yi'] > 0:
            signal = 'WEAK_BUY'
            confidence = 'MEDIUM'
            reason = '主力净流入，但金额不大'
        elif main_net < -1 and latest['net_mf_amount_yi'] < 0:
            signal = 'SELL'
            confidence = 'HIGH'
            reason = '主力大幅净流出，态度消极'
        elif main_net < 0 and latest['net_mf_amount_yi'] < 0:
            signal = 'WEAK_SELL'
            confidence = 'MEDIUM'
            reason = '主力净流出，注意风险'
        else:
            signal = 'NEUTRAL'
            confidence = 'LOW'
            reason = '资金流向不明显'
        
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'date': latest['trade_date'].strftime('%Y-%m-%d'),
            'main_net': main_net,  # 主力净流入（亿元）
            'retail_net': retail_net,  # 散户净流入（亿元）
            'total_net': latest['net_mf_amount_yi'],  # 总净流入（亿元）
            'lg_net': latest['buy_lg_amount_yi'] - latest['sell_lg_amount_yi'],  # 大单净流入
            'elg_net': latest['buy_elg_amount_yi'] - latest['sell_elg_amount_yi'],  # 特大单净流入
            'trend_3d': recent_3d,
            'trend': trend,
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'raw_data': latest
        }
    
    def to_message(self, result: dict) -> str:
        """转换为飞书消息格式"""
        if result is None:
            return f"❌ {self.stock_name} 数据获取失败"
        
        signal_emoji = {
            'BUY': '🚀', 'WEAK_BUY': '📈',
            'SELL': '🔻', 'WEAK_SELL': '📉',
            'NEUTRAL': '⚪'
        }.get(result['signal'], '⚪')
        
        confidence_text = {
            'HIGH': '高', 'MEDIUM': '中', 'LOW': '低'
        }.get(result['confidence'], '未知')
        
        msg = f"**{result['stock_name']} ({result['stock_code']})**\n"
        msg += f"📅 {result['date']} (Tushare Pro数据)\n\n"
        
        msg += f"💰 **资金流向（亿元）**\n"
        msg += f"  主力净流入: {result['main_net']:+.2f}\n"
        msg += f"  大单: {result['lg_net']:+.2f} | 特大单: {result['elg_net']:+.2f}\n"
        msg += f"  散户净流入: {result['retail_net']:+.2f}\n"
        msg += f"  总净流入: {result['total_net']:+.2f}\n\n"
        
        msg += f"📊 **近期趋势**: {result['trend']} ({result['trend_3d']:+.2f}亿/3日)\n\n"
        
        msg += f"🎯 **交易信号**: {signal_emoji} {result['signal']}\n"
        msg += f"📈 **置信度**: {confidence_text}\n"
        msg += f"💡 **理由**: {result['reason']}\n"
        
        return msg

def analyze_watchlist(watchlist):
    """分析自选股列表"""
    results = []
    
    print(f"\n{'='*70}")
    print("📊 Tushare Pro 资金流向分析")
    print(f"{'='*70}")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    for stock in watchlist:
        print(f"分析 {stock['name']}...", end=" ")
        
        strategy = TushareFlowStrategy(
            stock['code'], 
            stock['name'], 
            stock.get('market', 'SZ')
        )
        result = strategy.analyze()
        
        if result:
            results.append(result)
            print("✅")
        else:
            print("❌")
    
    return results

def generate_summary(results):
    """生成汇总报告"""
    if not results:
        return "暂无分析结果"
    
    # 按主力净流入排序
    sorted_results = sorted(results, key=lambda x: x['main_net'], reverse=True)
    
    msg = f"📊 **资金流向汇总** (Tushare Pro)\n"
    msg += f"分析股票: {len(results)}只 | 日期: {results[0]['date']}\n\n"
    
    # 流入TOP3
    inflow = [r for r in sorted_results if r['main_net'] > 0]
    if inflow:
        msg += "**🔴 主力流入 TOP**\n"
        for r in inflow[:3]:
            msg += f"  {r['stock_name']}: +{r['main_net']:.2f}亿 ({r['total_net']:+.2f}亿)\n"
        msg += "\n"
    
    # 流出TOP3
    outflow = [r for r in sorted_results if r['main_net'] < 0]
    if outflow:
        msg += "**🟢 主力流出 TOP**\n"
        for r in outflow[-3:]:
            msg += f"  {r['stock_name']}: {r['main_net']:.2f}亿 ({r['total_net']:+.2f}亿)\n"
        msg += "\n"
    
    # 强信号
    strong_signals = [r for r in results if r['signal'] in ['BUY', 'SELL']]
    if strong_signals:
        msg += "**🚨 强信号提醒**\n"
        for r in strong_signals:
            emoji = '🚀' if r['signal'] == 'BUY' else '🔻'
            msg += f"  {emoji} {r['stock_name']}: {r['reason']}\n"
    
    return msg

def main():
    """主函数"""
    # 自选股配置
    watchlist = [
        {"code": "000001", "name": "平安银行", "market": "SZ"},
        {"code": "600519", "name": "贵州茅台", "market": "SH"},
        {"code": "000858", "name": "五粮液", "market": "SZ"},
        {"code": "600362", "name": "江西铜业", "market": "SH"},
    ]
    
    # 分析
    results = analyze_watchlist(watchlist)
    
    if not results:
        print("\n❌ 未获取到任何数据")
        return
    
    # 打印详细结果
    print(f"\n{'='*70}")
    print("详细分析结果")
    print(f"{'='*70}\n")
    
    for result in results:
        strategy = TushareFlowStrategy(result['stock_code'], result['stock_name'])
        print(strategy.to_message(result))
        print("-" * 50)
    
    # 打印汇总
    print(f"\n{'='*70}")
    print(generate_summary(results))
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
