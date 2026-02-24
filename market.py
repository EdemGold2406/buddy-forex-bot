import yfinance as yf
import pandas as pd

# --- THE GOLDEN LIST ---
# These are the most liquid and predictable pairs for Price Action trading.
PAIRS = [
    "EURUSD=X",  # The King (Low Spread, Stable)
    "GBPJPY=X",  # The Dragon (High Volatility, Big Moves)
    "USDJPY=X",  # The Ninja (Strong Trends)
    "AUDUSD=X",  # The Aussie (Slow & Steady)
    "GC=F"       # Gold Futures (Respects Support/Resistance)
]

def get_market_data(pair_input):
    # Handle user variations (e.g., "Gold" -> "GC=F")
    if pair_input.upper() == "GOLD":
        ticker = "GC=F"
    elif "=" not in pair_input and "-" not in pair_input:
        ticker = f"{pair_input.upper()}=X"
    else:
        ticker = pair_input.upper()

    try:
        # Fetch 1-hour data for the last 5 days
        data = yf.download(ticker, period="5d", interval="1h", progress=False)
        
        if data.empty:
            return None

        # Clean Data
        current_price = float(data['Close'].iloc[-1])
        open_price = float(data['Open'].iloc[-1])
        high_price = float(data['High'].max())
        low_price = float(data['Low'].min())
        
        # Trend Filter (Simple 50 SMA)
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
        trend = "BULLISH" if current_price > sma_50 else "BEARISH"

        market_info = (
            f"Asset: {pair_input.upper()}\n"
            f"Price: {current_price:.4f}\n"
            f"Trend (50 SMA): {trend}\n"
            f"5-Day Range: {low_price:.4f} - {high_price:.4f}\n"
        )
        return market_info

    except Exception as e:
        return f"Error: {e}"

def scan_all_pairs():
    # --- THIS IS THE MISSING FUNCTION ---
    summary = []
    
    for ticker in PAIRS:
        try:
            data = yf.download(ticker, period="2d", interval="1h", progress=False)
            if not data.empty:
                # Calculate percent change to see if it's moving
                open_p = data['Open'].iloc[-1]
                close_p = data['Close'].iloc[-1]
                change_pct = ((close_p - open_p) / open_p) * 100
                
                # We only want pairs that are actually moving (>0.05%)
                if abs(change_pct) > 0.05:
                    name = "GOLD" if ticker == "GC=F" else ticker.replace("=X", "")
                    summary.append(f"{name}: Changed {change_pct:.2f}% in last hour.")
        except:
            continue
    
    if not summary:
        return "Market is sleeping. No significant moves on the Big 5."
    
    return "\n".join(summary)
