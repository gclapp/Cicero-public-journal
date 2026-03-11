#!/usr/bin/env python3
"""
fetch_stock_data.py - Fetch stock prices for PGNY and watchlist
Run daily before morning check-in
"""

import json
import urllib.request
from pathlib import Path
from datetime import datetime

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "stock-data.json"

# Free stock API (Alpha Vantage or similar - using Yahoo Finance via rapidapi or yfinance)
# For now, using a simple approach with Yahoo Finance query

def fetch_stock_price(symbol):
    """Fetch current stock price from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        result = data['chart']['result'][0]
        meta = result['meta']
        
        current_price = meta.get('regularMarketPrice', 0)
        previous_close = meta.get('previousClose', 0)
        
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        return {
            'symbol': symbol,
            'price': current_price,
            'change': change,
            'change_percent': change_percent,
            'previous_close': previous_close,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def fetch_all_stocks():
    """Fetch all stocks in watchlist + indices"""
    watchlist = ['PGNY', 'AAPL', 'NVDA']  # Progyny, Apple, NVIDIA
    indices = ['^GSPC', '^DJI']  # S&P 500, Dow Jones
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'stocks': {},
        'indices': {}
    }
    
    # Fetch individual stocks
    for symbol in watchlist:
        data = fetch_stock_price(symbol)
        if data:
            results['stocks'][symbol] = data
            print(f"✅ {symbol}: ${data['price']:.2f} ({data['change']:+.2f}, {data['change_percent']:+.2f}%)")
        else:
            print(f"❌ Failed to fetch {symbol}")
    
    # Fetch market indices
    for symbol in indices:
        data = fetch_stock_price(symbol)
        if data:
            # Format index names nicely
            name = 'S&P 500' if symbol == '^GSPC' else 'Dow Jones' if symbol == '^DJI' else symbol
            results['indices'][name] = data
            print(f"✅ {name}: {data['price']:,.2f} ({data['change']:+.2f}, {data['change_percent']:+.2f}%)")
        else:
            print(f"❌ Failed to fetch {symbol}")
    
    # Save to file
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def get_stock_summary():
    """Get formatted stock summary for check-ins"""
    if not DATA_FILE.exists():
        fetch_all_stocks()
    
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    stocks = data.get('stocks', {})
    indices = data.get('indices', {})
    
    summary = "📈 **Markets**\n\n"
    
    # Market Indices first
    summary += "**Indices:**\n"
    for name, s in indices.items():
        emoji = "🟢" if s['change'] >= 0 else "🔴"
        summary += f"{emoji} {name}: {s['price']:,.2f} ({s['change_percent']:+.2f}%)\n"
    
    summary += "\n**Your Watchlist:**\n"
    
    # PGNY first (most important)
    if 'PGNY' in stocks:
        s = stocks['PGNY']
        emoji = "🟢" if s['change'] >= 0 else "🔴"
        summary += f"{emoji} **PGNY:** ${s['price']:.2f} ({s['change']:+.2f}, {s['change_percent']:+.2f}%)\n"
    
    # Other stocks
    for symbol, s in stocks.items():
        if symbol != 'PGNY':
            emoji = "🟢" if s['change'] >= 0 else "🔴"
            summary += f"{emoji} {symbol}: ${s['price']:.2f} ({s['change']:+.2f}%)\n"
    
    return summary

if __name__ == "__main__":
    print("Fetching stock data...")
    results = fetch_all_stocks()
    print("\nStock summary for check-in:")
    print(get_stock_summary())
