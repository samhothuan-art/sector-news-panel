#!/usr/bin/env python3
"""
A-Stock Price Checker - Get current stock prices from Tushare for China A-shares.
Uses tushare token from TOOLS.md
"""

import sys
import os
import json
import re

# Try to import tushare
try:
    import tushare as ts
except ImportError:
    print("Error: tushare not installed. Run: pip3 install tushare")
    sys.exit(1)

# Tushare token
TUSHARE_TOKEN = "9e002cf5c323daadf44e180b80ae9489a543a5709f05edf1609e377d"

# Initialize tushare
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

def normalize_symbol(symbol: str) -> str:
    """Convert various symbol formats to tushare format (e.g., 000977.SZ)."""
    # Remove any suffix first
    symbol = symbol.upper().strip()
    
    # Handle formats like 000977.SZ, 000977SZ, 512480.SH, etc.
    if '.' in symbol:
        parts = symbol.split('.')
        return f"{parts[0]}.{parts[1]}"
    
    # Pure number - need to determine exchange
    if symbol.isdigit():
        # Shanghai: 6xxxxx (main), 5xxxxx (ETF/funds), 9xxxxx (B shares)
        # Shenzhen: 0xxxxx, 3xxxxx, 2xxxxx (ChiNext)
        if symbol.startswith('6') or symbol.startswith('5') or symbol.startswith('9'):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"
    
    # Handle format like 000977SZ
    if symbol.endswith('SH') or symbol.endswith('SZ'):
        code = symbol[:-2]
        suffix = symbol[-2:]
        return f"{code}.{suffix}"
    
    return symbol

def get_stock_price(symbol: str, cost_price: float = None) -> dict:
    """Get current stock price for a given A-share symbol."""
    try:
        normalized = normalize_symbol(symbol)
        ts_code = normalized.replace('.', '')
        
        # Determine if it's an ETF/fund (starts with 5, 1, or 15/16/18)
        code = normalized.split('.')[0]
        is_fund = code.startswith('5') or code.startswith('1') or code.startswith('15') or code.startswith('16') or code.startswith('18')
        
        # Get daily data (most recent)
        if is_fund:
            df = pro.fund_daily(ts_code=normalized, limit=1)
        else:
            df = pro.daily(ts_code=normalized, limit=1)
        
        if df.empty:
            return {"error": f"No data found for {symbol}"}
        
        latest = df.iloc[0]
        
        # Get basic info
        name = symbol
        industry = ''
        
        if is_fund:
            try:
                fund_basic = pro.fund_basic(ts_code=normalized, fields='name,fund_type')
                if not fund_basic.empty:
                    name = fund_basic.iloc[0]['name']
                    industry = fund_basic.iloc[0].get('fund_type', 'ETF/Fund')
            except:
                pass
        else:
            try:
                basic = pro.stock_basic(ts_code=normalized, fields='name,industry')
                if not basic.empty:
                    name = basic.iloc[0]['name']
                    industry = basic.iloc[0].get('industry', '')
            except:
                pass
        
        result = {
            "symbol": symbol,
            "ts_code": normalized,
            "name": name,
            "industry": industry,
            "date": latest['trade_date'],
            "open": float(latest['open']),
            "high": float(latest['high']),
            "low": float(latest['low']),
            "close": float(latest['close']),
            "pre_close": float(latest['pre_close']),
            "change": float(latest['change']),
            "pct_change": float(latest['pct_chg']),
            "volume": int(latest['vol']),  # in lots (手)
            "amount": float(latest['amount']),  # in 千元
        }
        
        # Add cost basis calculation if provided
        if cost_price is not None:
            result["cost_price"] = cost_price
            result["profit_loss"] = result["close"] - cost_price
            result["profit_loss_pct"] = ((result["close"] - cost_price) / cost_price) * 100
        
        return result
        
    except Exception as e:
        return {"error": f"Could not get stock price for {symbol}: {str(e)}"}

def format_output(data: dict) -> str:
    """Format stock data in a readable output."""
    if "error" in data:
        return f"Error: {data['error']}"
    
    symbol = data['symbol']
    name = data['name']
    price = data['close']
    change = data['change']
    pct_change = data['pct_change']
    volume = data['volume']
    
    # Format price (A-shares in CNY)
    price_str = f"¥{price:.2f}"
    
    # Format change with arrow
    if change > 0:
        change_str = f"▲{change:.2f}"
        pct_str = f"+{pct_change:.2f}%"
        emoji = "🟥"
    elif change < 0:
        change_str = f"▼{abs(change):.2f}"
        pct_str = f"{pct_change:.2f}%"
        emoji = "🟩"
    else:
        change_str = "—"
        pct_str = "0.00%"
        emoji = "⬜"
    
    # Format volume (convert from lots to shares/10k)
    volume_shares = volume * 100  # 1 lot = 100 shares
    if volume_shares >= 100_000_000:
        volume_str = f"{volume_shares/100_000_000:.2f}亿股"
    elif volume_shares >= 10_000:
        volume_str = f"{volume_shares/10_000:.2f}万股"
    else:
        volume_str = f"{volume_shares}股"
    
    output = f"{emoji} {name} ({symbol})\n"
    output += f"   价格: {price_str} {change_str} ({pct_str})\n"
    output += f"   成交量: {volume_str}"
    
    # Add cost basis info if available
    if "cost_price" in data:
        cost = data['cost_price']
        pl = data['profit_loss']
        pl_pct = data['profit_loss_pct']
        
        pl_emoji = "🟢" if pl >= 0 else "🔴"
        pl_sign = "+" if pl >= 0 else ""
        
        output += f"\n   成本: ¥{cost:.2f}"
        output += f"\n   盈亏: {pl_emoji} {pl_sign}{pl:.2f} ({pl_sign}{pl_pct:.2f}%)"
    
    return output

def main():
    if len(sys.argv) < 2:
        print("Usage: a-stock-price <SYMBOL> [COST_PRICE]")
        print("Examples:")
        print("  a-stock-price 000977")
        print("  a-stock-price 000977.SZ 63.46")
        print("  a-stock-price 512480 1.617")
        sys.exit(1)
    
    symbol = sys.argv[1]
    cost_price = None
    
    if len(sys.argv) >= 3:
        try:
            cost_price = float(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid cost price '{sys.argv[2]}', ignoring")
    
    result = get_stock_price(symbol, cost_price)
    print(format_output(result))

if __name__ == "__main__":
    main()
