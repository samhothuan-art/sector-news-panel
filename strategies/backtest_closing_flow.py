#!/usr/bin/env python3
"""
尾盘资金流向策略回测
策略：每周一、二、三选股，持股一周，3只股票，70%仓位
回测区间：过去8个月（2025年6月-2026年2月）
"""

import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

TUSHARE_TOKEN = '9e002cf5c323daadf44e180b80ae9489a543a5709f05edf1609e377d'

class ClosingFlowBacktest:
    """
    尾盘资金流向策略回测框架
    """
    
    def __init__(self, start_date='20250601', end_date='20260225', 
                 initial_cash=1000000, position_pct=0.7):
        """
        Args:
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_cash: 初始资金（默认100万）
            position_pct: 仓位比例（70%）
        """
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.position_pct = position_pct
        self.pro = ts.pro_api(TUSHARE_TOKEN)
        
        # 交易记录
        self.trades = []
        self.daily_nav = []
        
    def get_trade_dates(self):
        """获取交易日历"""
        df = self.pro.trade_cal(start_date=self.start_date, 
                                end_date=self.end_date, 
                                is_open='1')
        return df['cal_date'].tolist()
    
    def get_weekly_trade_dates(self, trade_dates):
        """
        获取每周一、二、三的交易日
        """
        weekly_dates = []
        
        for i, date in enumerate(trade_dates):
            # 转换为日期对象
            dt = datetime.strptime(date, '%Y%m%d')
            weekday = dt.weekday()  # 周一=0, 周二=1, 周三=2
            
            # 只选周一、二、三
            if weekday in [0, 1, 2]:
                weekly_dates.append(date)
        
        return weekly_dates
    
    def get_moneyflow_data(self, trade_date):
        """获取某日的资金流向数据"""
        try:
            df = self.pro.moneyflow(trade_date=trade_date)
            
            if df is None or df.empty:
                return None
            
            # 计算主力净流入
            df['main_net'] = (df['buy_elg_amount'] + df['buy_lg_amount'] - 
                             df['sell_elg_amount'] - df['sell_lg_amount'])
            
            # 过滤条件
            df = df[df['main_net'] > 0]  # 主力净流入为正
            df = df.sort_values('main_net', ascending=False)
            
            return df.head(50)  # 取前50只
            
        except Exception as e:
            print(f"获取{trade_date}资金流向失败: {e}")
            return None
    
    def get_stock_basic(self, ts_codes):
        """获取股票基本信息"""
        try:
            df = self.pro.stock_basic(ts_code=','.join(ts_codes), 
                                     fields='ts_code,name,industry,market')
            return df
        except:
            return None
    
    def select_stocks(self, trade_date, num_stocks=3):
        """
        选股逻辑：从八大板块中，选主力流入最多的
        """
        # 八大板块关键词
        sector_keywords = {
            'AI算力': ['通信设备', '元器件', '软件服务'],
            '半导体': ['半导体', '电子', '芯片'],
            '机器人': ['专用机械', '通用机械', '自动化设备'],
            '有色金属': ['有色金属', '贵金属', '稀有金属'],
            '新能源': ['电气设备', '电源设备', '新能源'],
            '消费': ['食品饮料', '医药', '旅游', '商贸'],
            '军工': ['航空航天', '船舶', '军工'],
            '高股息': ['银行', '电力', '煤炭', '交通运输']
        }
        
        # 获取资金流向
        moneyflow = self.get_moneyflow_data(trade_date)
        
        if moneyflow is None:
            return []
        
        # 获取基本信息
        ts_codes = moneyflow['ts_code'].tolist()[:30]
        basic_info = self.get_stock_basic(ts_codes)
        
        if basic_info is not None:
            moneyflow = moneyflow.merge(basic_info, on='ts_code', how='left')
        
        # 筛选八大板块的股票
        selected = []
        
        for _, row in moneyflow.iterrows():
            if len(selected) >= num_stocks:
                break
            
            industry = str(row.get('industry', ''))
            
            # 检查是否属于八大板块
            for sector, keywords in sector_keywords.items():
                if any(kw in industry for kw in keywords):
                    selected.append({
                        'ts_code': row['ts_code'],
                        'name': row.get('name', row['ts_code']),
                        'industry': industry,
                        'sector': sector,
                        'main_net': row['main_net'],
                        'trade_date': trade_date
                    })
                    break
        
        return selected[:num_stocks]
    
    def get_buy_price(self, ts_code, trade_date):
        """获取买入价（次日开盘价）"""
        try:
            # 获取次日数据
            next_date = (datetime.strptime(trade_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
            df = self.pro.daily(ts_code=ts_code, start_date=next_date, end_date=next_date)
            
            if df is not None and not df.empty:
                return df.iloc[0]['open']
            return None
        except:
            return None
    
    def get_sell_price(self, ts_code, buy_date):
        """获取卖出价（持有一周后收盘价）"""
        try:
            # 获取持有一周的数据
            start_dt = datetime.strptime(buy_date, '%Y%m%d')
            end_dt = start_dt + timedelta(days=7)
            end_date = end_dt.strftime('%Y%m%d')
            
            df = self.pro.daily(ts_code=ts_code, start_date=buy_date, end_date=end_date)
            
            if df is not None and len(df) >= 5:
                # 持有一周（约5个交易日）后的收盘价
                return df.iloc[4]['close']
            elif df is not None and not df.empty:
                return df.iloc[-1]['close']
            return None
        except:
            return None
    
    def run_backtest(self):
        """运行回测"""
        print("="*70)
        print("🚀 尾盘资金流向策略回测")
        print("="*70)
        print(f"回测区间: {self.start_date} - {self.end_date}")
        print(f"初始资金: ¥{self.initial_cash:,.0f}")
        print(f"仓位比例: {self.position_pct*100:.0f}%")
        print(f"选股数量: 3只")
        print(f"持股周期: 1周")
        print(f"交易时间: 每周一、二、三")
        print("="*70)
        print()
        
        # 获取交易日历
        trade_dates = self.get_trade_dates()
        weekly_dates = self.get_weekly_trade_dates(trade_dates)
        
        print(f"总交易日: {len(trade_dates)}天")
        print(f"交易次数: {len(weekly_dates)}次")
        print()
        
        cash = self.initial_cash
        current_positions = []
        
        for i, trade_date in enumerate(weekly_dates):
            print(f"\n{'='*70}")
            print(f"📅 第{i+1}次交易 ({trade_date})")
            print(f"{'='*70}")
            
            # 检查是否有持仓到期
            positions_to_sell = []
            for pos in current_positions:
                sell_date = (datetime.strptime(pos['buy_date'], '%Y%m%d') + 
                           timedelta(days=7)).strftime('%Y%m%d')
                if trade_date >= sell_date:
                    positions_to_sell.append(pos)
            
            # 卖出到期的股票
            for pos in positions_to_sell:
                sell_price = self.get_sell_price(pos['ts_code'], pos['buy_date'])
                if sell_price:
                    sell_value = pos['shares'] * sell_price * (1 - 0.001)  # 扣除手续费
                    profit = sell_value - pos['cost']
                    profit_pct = profit / pos['cost'] * 100
                    
                    cash += sell_value
                    
                    self.trades.append({
                        'ts_code': pos['ts_code'],
                        'name': pos['name'],
                        'buy_date': pos['buy_date'],
                        'sell_date': trade_date,
                        'buy_price': pos['buy_price'],
                        'sell_price': sell_price,
                        'shares': pos['shares'],
                        'profit': profit,
                        'profit_pct': profit_pct
                    })
                    
                    print(f"📤 卖出 {pos['name']} @ ¥{sell_price:.2f} | 收益: {profit:+.0f} ({profit_pct:+.2f}%)")
                
                current_positions.remove(pos)
            
            # 选股
            selected = self.select_stocks(trade_date)
            
            if not selected:
                print("❌ 本日无符合条件股票")
                continue
            
            print(f"\n📊 选中股票:")
            for s in selected:
                print(f"  • {s['name']} ({s['sector']}) 主力流入: {s['main_net']/10000:.0f}万")
            
            # 计算可用资金
            available_cash = cash * self.position_pct
            cash_per_stock = available_cash / 3  # 每只股固定仓位
            
            # 买入
            for stock in selected:
                buy_price = self.get_buy_price(stock['ts_code'], trade_date)
                
                if buy_price and buy_price > 0:
                    # 确保至少买100股
                    shares = max(100, int(cash_per_stock / buy_price / 100) * 100)
                    cost = shares * buy_price * (1 + 0.001)  # 含手续费
                    
                    if cost <= cash and shares >= 100:
                        cash -= cost
                        current_positions.append({
                            'ts_code': stock['ts_code'],
                            'name': stock['name'],
                            'buy_date': trade_date,
                            'buy_price': buy_price,
                            'shares': shares,
                            'cost': cost
                        })
                        
                        print(f"📥 买入 {stock['name']} {shares}股 @ ¥{buy_price:.2f} (成本: {cost:.0f})")
        
        # 回测结束，清算剩余持仓
        print(f"\n{'='*70}")
        print("📊 回测结束，清算持仓")
        print(f"{'='*70}")
        
        for pos in current_positions:
            # 使用最后一日收盘价
            try:
                df = self.pro.daily(ts_code=pos['ts_code'], 
                                   start_date=self.end_date, 
                                   end_date=self.end_date)
                if df is not None and not df.empty:
                    sell_price = df.iloc[0]['close']
                    sell_value = pos['shares'] * sell_price * (1 - 0.001)
                    profit = sell_value - pos['cost']
                    profit_pct = profit / pos['cost'] * 100
                    
                    cash += sell_value
                    
                    self.trades.append({
                        'ts_code': pos['ts_code'],
                        'name': pos['name'],
                        'buy_date': pos['buy_date'],
                        'sell_date': self.end_date,
                        'buy_price': pos['buy_price'],
                        'sell_price': sell_price,
                        'shares': pos['shares'],
                        'profit': profit,
                        'profit_pct': profit_pct
                    })
                    
                    print(f"📤 清仓 {pos['name']} @ ¥{sell_price:.2f} | 收益: {profit:+.0f} ({profit_pct:+.2f}%)")
            except:
                pass
        
        # 生成报告
        self.generate_report(cash)
    
    def generate_report(self, final_cash):
        """生成回测报告"""
        print(f"\n{'='*70}")
        print("📈 回测报告")
        print(f"{'='*70}\n")
        
        if not self.trades:
            print("❌ 无交易记录")
            return
        
        trades_df = pd.DataFrame(self.trades)
        
        # 总体指标
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['profit'] > 0])
        losing_trades = len(trades_df[trades_df['profit'] <= 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_profit = trades_df['profit'].sum()
        avg_profit = trades_df['profit_pct'].mean()
        max_profit = trades_df['profit_pct'].max()
        max_loss = trades_df['profit_pct'].min()
        
        total_return = (final_cash - self.initial_cash) / self.initial_cash * 100
        
        print(f"初始资金: ¥{self.initial_cash:,.0f}")
        print(f"最终资金: ¥{final_cash:,.0f}")
        print(f"总收益: ¥{final_cash - self.initial_cash:,.0f} ({total_return:+.2f}%)")
        print()
        print(f"总交易次数: {total_trades}")
        print(f"盈利次数: {winning_trades}")
        print(f"亏损次数: {losing_trades}")
        print(f"胜率: {win_rate:.1f}%")
        print()
        print(f"平均收益: {avg_profit:.2f}%")
        print(f"最大盈利: {max_profit:.2f}%")
        print(f"最大亏损: {max_loss:.2f}%")
        print()
        
        # 按板块统计
        print("板块表现:")
        sector_perf = trades_df.groupby('name')['profit_pct'].mean().sort_values(ascending=False)
        for name, perf in sector_perf.head(10).items():
            print(f"  {name}: {perf:+.2f}%")
        
        # 保存详细交易记录
        output_dir = '/Users/opensamhot/.openclaw/workspace/data'
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        trades_df.to_csv(f'{output_dir}/backtest_trades.csv', index=False, encoding='utf-8-sig')
        print(f"\n✅ 交易记录已保存: {output_dir}/backtest_trades.csv")

def main():
    """主函数"""
    # 先做2个月回测（2025年12月-2026年2月）
    backtest = ClosingFlowBacktest(
        start_date='20251201',
        end_date='20260225',
        initial_cash=1000000,
        position_pct=0.7
    )
    
    backtest.run_backtest()

if __name__ == "__main__":
    main()
