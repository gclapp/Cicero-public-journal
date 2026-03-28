#!/usr/bin/env python3
"""
fetch_stock_data.py - Fetch stock prices for PGNY and watchlist with 30-day rolling history
Run daily before morning check-in
"""

import json
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "stock-data.json"
HISTORY_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "stock-history.json"

WATCHLIST = ['PGNY', 'AAPL', 'NVDA', 'OMDA']
INDICES = ['^GSPC', '^DJI']

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

def load_history():
    """Load the 30-day rolling history"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {
        "metadata": {
            "created": datetime.now().isoformat(),
            "description": "30-day rolling stock price history",
            "stocks": WATCHLIST,
            "max_days": 30
        },
        "history": {symbol: [] for symbol in WATCHLIST}
    }

def save_history(history):
    """Save the 30-day rolling history"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def add_price_to_history(symbol, price, date_str):
    """Add a daily closing price to the history, maintaining 30-day window"""
    history = load_history()
    
    if symbol not in history['history']:
        history['history'][symbol] = []
    
    # Check if we already have an entry for today
    symbol_history = history['history'][symbol]
    for entry in symbol_history:
        if entry['date'] == date_str:
            # Update existing entry
            entry['price'] = price
            save_history(history)
            return
    
    # Add new entry
    symbol_history.append({
        'date': date_str,
        'price': price
    })
    
    # Sort by date and keep only last 30 days
    symbol_history.sort(key=lambda x: x['date'])
    if len(symbol_history) > 30:
        symbol_history[:] = symbol_history[-30:]
    
    save_history(history)

def get_price_30_days_ago(symbol):
    """Get the price from 30 days ago, or earliest available if less than 30 days"""
    history = load_history()
    symbol_history = history['history'].get(symbol, [])
    
    if not symbol_history:
        return None
    
    today = datetime.now().date()
    target_date = today - timedelta(days=30)
    
    # Find the closest entry to 30 days ago
    for entry in reversed(symbol_history):
        entry_date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
        if entry_date <= target_date:
            return entry['price']
    
    # If no entry from 30 days ago, return the earliest available
    return symbol_history[0]['price'] if symbol_history else None

def calculate_30_day_change(symbol, current_price):
    """Calculate 30-day change percentage"""
    price_30d_ago = get_price_30_days_ago(symbol)
    
    if price_30d_ago and price_30d_ago > 0:
        change = current_price - price_30d_ago
        change_percent = (change / price_30d_ago) * 100
        return {
            'price_30d_ago': price_30d_ago,
            'change': change,
            'change_percent': change_percent,
            'days_of_data': min(30, len(load_history()['history'].get(symbol, [])))
        }
    
    return {
        'price_30d_ago': None,
        'change': 0,
        'change_percent': 0,
        'days_of_data': 0
    }

def fetch_all_stocks(verbose=True):
    """Fetch all stocks in watchlist + indices and update history"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'stocks': {},
        'indices': {}
    }
    
    # Fetch individual stocks
    for symbol in WATCHLIST:
        data = fetch_stock_price(symbol)
        if data:
            # Add to 30-day history
            add_price_to_history(symbol, data['price'], today)
            
            # Calculate 30-day change
            change_30d = calculate_30_day_change(symbol, data['price'])
            data['change_30d'] = change_30d
            
            results['stocks'][symbol] = data
            if verbose:
                print(f"✅ {symbol}: ${data['price']:.2f} (30d: {change_30d['change_percent']:+.2f}%)")
        else:
            if verbose:
                print(f"❌ Failed to fetch {symbol}")
    
    # Fetch market indices (don't track history for indices)
    for symbol in INDICES:
        data = fetch_stock_price(symbol)
        if data:
            name = 'S&P 500' if symbol == '^GSPC' else 'Dow Jones' if symbol == '^DJI' else symbol
            results['indices'][name] = data
            if verbose:
                print(f"✅ {name}: {data['price']:,.2f} ({data['change_percent']:+.2f}%)")
        else:
            if verbose:
                print(f"❌ Failed to fetch {symbol}")
    
    # Save current snapshot
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def get_stock_summary():
    """Get formatted stock summary for check-ins with 30-day changes"""
    if not DATA_FILE.exists():
        fetch_all_stocks()
    
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    stocks = data.get('stocks', {})
    indices = data.get('indices', {})
    
    summary = "📈 **Markets (30-Day View)**\n\n"
    
    # Market Indices first
    summary += "**Indices:**\n"
    for name, s in indices.items():
        emoji = "🟢" if s['change'] >= 0 else "🔴"
        summary += f"{emoji} {name}: {s['price']:,.2f} ({s['change_percent']:+.2f}% today)\n"
    
    summary += "\n**Your Watchlist (30-Day Change):**\n"
    
    # PGNY first (most important)
    if 'PGNY' in stocks:
        s = stocks['PGNY']
        change_30d = s.get('change_30d', {})
        change_pct = change_30d.get('change_percent', 0)
        days = change_30d.get('days_of_data', 0)
        emoji = "🟢" if change_pct >= 0 else "🔴"
        days_text = f"{days}d" if days < 30 else "30d"
        summary += f"{emoji} **PGNY:** ${s['price']:.2f} ({change_pct:+.2f}% / {days_text})\n"
    
    # Other stocks
    for symbol, s in stocks.items():
        if symbol != 'PGNY':
            change_30d = s.get('change_30d', {})
            change_pct = change_30d.get('change_percent', 0)
            days = change_30d.get('days_of_data', 0)
            emoji = "🟢" if change_pct >= 0 else "🔴"
            days_text = f"{days}d" if days < 30 else "30d"
            summary += f"{emoji} {symbol}: ${s['price']:.2f} ({change_pct:+.2f}% / {days_text})\n"
    
    return summary

def get_detailed_summary():
    """Get detailed summary with both daily and 30-day changes"""
    if not DATA_FILE.exists():
        fetch_all_stocks()
    
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    stocks = data.get('stocks', {})
    indices = data.get('indices', {})
    
    summary = "📈 **Stock Market Update**\n\n"
    
    # Market Indices
    summary += "**Market Indices:**\n"
    for name, s in indices.items():
        emoji = "🟢" if s['change'] >= 0 else "🔴"
        summary += f"{emoji} {name}: {s['price']:,.2f} ({s['change']:+.2f}, {s['change_percent']:+.2f}% today)\n"
    
    summary += "\n**Watchlist (30-Day Rolling):**\n"
    
    for symbol in ['PGNY', 'AAPL', 'NVDA', 'OMDA']:
        if symbol in stocks:
            s = stocks[symbol]
            change_30d = s.get('change_30d', {})
            change_30d_pct = change_30d.get('change_percent', 0)
            days = change_30d.get('days_of_data', 0)
            
            # Use 30-day change for emoji
            emoji = "🟢" if change_30d_pct >= 0 else "🔴"
            days_text = f"{days}d history" if days < 30 else "30d"
            
            summary += f"\n{emoji} **{symbol}:** ${s['price']:.2f}\n"
            summary += f"   ├─ Today: {s['change']:+.2f} ({s['change_percent']:+.2f}%)\n"
            summary += f"   └─ 30-Day: {change_30d_pct:+.2f}% ({days_text})\n"
    
    return summary

if __name__ == "__main__":
    import sys
    
    # Check if --summary flag passed (for check-ins, use clean format)
    is_summary = '--summary' in sys.argv
    
    # Fetch data (verbose only if not summary mode)
    if not is_summary:
        print("Fetching stock data with 30-day history...")
    results = fetch_all_stocks(verbose=not is_summary)
    
    if is_summary:
        # Clean format for check-in emails - just the essential data
        print(get_stock_summary())
    else:
        # Full format for manual runs
        print("\n" + "="*50)
        print("Stock summary for check-in:")
        print("="*50)
        print(get_stock_summary())
        print("\n" + "="*50)
        print("Detailed summary:")
        print("="*50)
        print(get_detailed_summary())