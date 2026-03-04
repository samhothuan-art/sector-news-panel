#!/usr/bin/env python3
"""
尾盘资金流向策略
监控 14:30-15:00 主力资金动向，用于次日交易决策
"""

import adata
import pandas as pd
from datetime import datetime, time, timedelta
import warnings
warnings.filterwarnings('ignore')

class ClosingFlowStrategy:
    """
    尾盘资金流向策略
    
    核心逻辑：
    1. 尾盘（14:30-15:00）主力大幅流入 → 次日高开概率大
    2. 尾盘主力大幅流出 → 次日低开概率大
    3. 结合价格形态判断真假突破
    """
    
    def __init__(self, stock_code: str, stock_name: str):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.data = None
    
    def get_closing_flow(self, date: datetime = None):
        """获取指定日期的尾盘资金流向"""
        if date is None:
            date = datetime.now()
        
        try:
            # 获取分钟级资金流向（百度数据源）
            df = adata.stock.market.baidu_capital_flow.get_capital_flow_min(
                stock_code=self.stock_code
            )
            df['trade_time'] = pd.to_datetime(df['trade_time'])
            
            # 过滤指定日期
            df['date'] = df['trade_time'].dt.date
            target_date = date.date()
            df = df[df['date'] == target_date]
            
            if df.empty:
                return None
            
            # 过滤尾盘时间 14:30-15:00
            df['time_only'] = df['trade_time'].dt.time
            closing_start = time(14, 30)
            closing_end = time(15, 0)
            
            closing_df = df[(df['time_only'] >= closing_start) & 
                          (df['time_only'] <= closing_end)]
            
            if closing_df.empty:
                return None
            
            # 计算尾盘净流入（收盘累计 - 14:30累计）
            first = closing_df.iloc[0]
            last = closing_df.iloc[-1]
            
            return {
                'main_flow': (last['main_net_inflow'] - first['main_net_inflow']) / 1e10,  # 亿元
                'lg_flow': (last['lg_net_inflow'] - first['lg_net_inflow']) / 1e10,
                'max_flow': (last['max_net_inflow'] - first['max_net_inflow']) / 1e10,
                'sm_flow': (last['sm_net_inflow'] - first['sm_net_inflow']) / 1e10,
            }
            
        except Exception as e:
            print(f"获取{self.stock_name}资金流向失败: {e}")
            return None
    
    def get_price_info(self, date: datetime = None):
        """获取当日价格信息"""
        if date is None:
            date = datetime.now()
        
        try:
            df = adata.stock.market.baidu_capital_flow.get_capital_flow_min(
                stock_code=self.stock_code
            )
            df['trade_time'] = pd.to_datetime(df['trade_time'])
            df['date'] = df['trade_time'].dt.date
            target_date = date.date()
            df = df[df['date'] == target_date]
            
            if df.empty:
                return None
            
            # 获取当日价格信息（从资金流向数据中提取）
            # 注意：百度数据中没有价格，需要从其他接口获取
            # 这里简化处理
            return {
                'close': None,  # 需要从其他接口获取
                'volume': None,
            }
            
        except:
            return None
    
    def analyze(self, date: datetime = None):
        """
        分析尾盘资金流向并给出交易建议
        
        Returns:
            dict: 分析结果
        """
        flow = self.get_closing_flow(date)
        
        if flow is None:
            return None
        
        main_flow = flow['main_flow']
        max_flow = flow['max_flow']
        
        # 判断信号强度
        if main_flow > 1 and max_flow > 0.5:
            signal = 'STRONG_BUY'
            confidence = 'HIGH'
            reason = '尾盘主力大幅流入，超大单积极抢筹'
        elif main_flow > 0.5:
            signal = 'BUY'
            confidence = 'MEDIUM'
            reason = '尾盘主力资金流入，态度偏多'
        elif main_flow < -1 and max_flow < -0.5:
            signal = 'STRONG_SELL'
            confidence = 'HIGH'
            reason = '尾盘主力大幅流出，超大单出货'
        elif main_flow < -0.5:
            signal = 'SELL'
            confidence = 'MEDIUM'
            reason = '尾盘主力资金流出，态度偏空'
        else:
            signal = 'NEUTRAL'
            confidence = 'LOW'
            reason = '尾盘资金流向不明显'
        
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'date': (date or datetime.now()).strftime('%Y-%m-%d'),
            'main_flow': main_flow,
            'max_flow': max_flow,
            'lg_flow': flow['lg_flow'],
            'sm_flow': flow['sm_flow'],
            'signal': signal,
            'confidence': confidence,
            'reason': reason
        }
    
    def to_message(self, result: dict) -> str:
        """转换为飞书消息格式"""
        if result is None:
            return f"❌ {self.stock_name} 数据获取失败"
        
        signal_emoji = {
            'STRONG_BUY': '🚀', 'BUY': '📈',
            'STRONG_SELL': '🔻', 'SELL': '📉',
            'NEUTRAL': '⚪'
        }.get(result['signal'], '⚪')
        
        confidence_text = {
            'HIGH': '高', 'MEDIUM': '中', 'LOW': '低'
        }.get(result['confidence'], '未知')
        
        msg = f"**{result['stock_name']} ({result['stock_code']})**\n"
        msg += f"📅 {result['date']} 尾盘分析\n\n"
        
        msg += f"💰 **资金流向**\n"
        msg += f"  主力: {result['main_flow']:+.2f}亿\n"
        msg += f"  超大单: {result['max_flow']:+.2f}亿\n"
        msg += f"  大单: {result['lg_flow']:+.2f}亿\n\n"
        
        msg += f"🎯 **交易信号**: {signal_emoji} {result['signal']}\n"
        msg += f"📊 **置信度**: {confidence_text}\n"
        msg += f"💡 **理由**: {result['reason']}\n"
        
        return msg

def analyze_watchlist(watchlist: list, date: datetime = None):
    """分析自选股的尾盘资金流向"""
    results = []
    
    print(f"\n{'='*60}")
    print(f"📊 尾盘资金流向策略分析")
    print(f"{'='*60}")
    print(f"分析时间: {(date or datetime.now()).strftime('%Y-%m-%d %H:%M')}\n")
    
    for stock in watchlist:
        print(f"分析 {stock['name']}...", end=" ")
        
        strategy = ClosingFlowStrategy(stock['code'], stock['name'])
        result = strategy.analyze(date)
        
        if result:
            results.append(result)
            print("✅")
        else:
            print("❌")
    
    return results

def generate_summary(results: list) -> str:
    """生成汇总报告"""
    if not results:
        return "暂无分析结果"
    
    # 按主力流入排序
    sorted_results = sorted(results, key=lambda x: x['main_flow'], reverse=True)
    
    msg = f"📊 **尾盘资金流向汇总**\n"
    msg += f"分析股票: {len(results)}只\n\n"
    
    # 流入TOP3
    inflow = [r for r in sorted_results if r['main_flow'] > 0]
    if inflow:
        msg += "**🔴 主力流入**\n"
        for r in inflow[:3]:
            msg += f"  {r['stock_name']}: +{r['main_flow']:.2f}亿\n"
        msg += "\n"
    
    # 流出TOP3
    outflow = [r for r in sorted_results if r['main_flow'] < 0]
    if outflow:
        msg += "**🟢 主力流出**\n"
        for r in outflow[-3:]:
            msg += f"  {r['stock_name']}: {r['main_flow']:.2f}亿\n"
        msg += "\n"
    
    # 强信号
    strong_signals = [r for r in results if r['signal'] in ['STRONG_BUY', 'STRONG_SELL']]
    if strong_signals:
        msg += "**🚨 强信号提醒**\n"
        for r in strong_signals:
            emoji = '🚀' if r['signal'] == 'STRONG_BUY' else '🔻'
            msg += f"  {emoji} {r['stock_name']}: {r['reason']}\n"
    
    return msg

def main():
    """主函数"""
    # 策略暂停警告
    print(f"\n{'='*60}")
    print("⚠️  策略已暂停 - 数据准确性存疑")
    print(f"{'='*60}")
    print("\n原因：数据源（adata 百度接口）返回的数据存在以下问题：")
    print("  1. 时间悖论：非交易时间返回了全天完整数据")
    print("  2. 数值异常：主力流入金额与实际盘面不符")
    print("  3. 日期标记可能错误")
    print("\n建议操作：")
    print("  • 用同花顺/东方财富APP验证数据准确性")
    print("  • 等待数据源修复或更换数据源（如Tushare Pro）")
    print("  • 在交易时段（9:30-15:00）再次测试")
    print(f"{'='*60}\n")
    return
    
    # ========== 以下代码暂停执行 ==========
    
    # 自选股
    watchlist = [
        {"code": "000001", "name": "平安银行"},
        {"code": "600519", "name": "贵州茅台"},
        {"code": "000858", "name": "五粮液"},
        {"code": "600362", "name": "江西铜业"},
    ]
    
    # 分析（默认分析今天）
    results = analyze_watchlist(watchlist)
    
    # 打印详细结果
    print(f"\n{'='*60}")
    print("详细分析结果")
    print(f"{'='*60}\n")
    
    for result in results:
        strategy = ClosingFlowStrategy(result['stock_code'], result['stock_name'])
        print(strategy.to_message(result))
        print("-" * 40)
    
    # 打印汇总
    print(f"\n{'='*60}")
    print(generate_summary(results))
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
