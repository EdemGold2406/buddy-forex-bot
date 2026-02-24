import yfinance as yf
import pandas as pd
import mplfinance as mpf
import os

# --- THE BIG 5 ---
PAIRS = ["EURUSD=X", "GBPJPY=X", "USDJPY=X", "AUDUSD=X", "GC=F"]

def get_market_data(pair_input):
    if pair_input.upper() == "GOLD": ticker = "GC=F"
    elif "=" not in pair_input and "-" not in pair_input: ticker = f"{pair_input.upper()}=X"
    else: ticker = pair_input.upper()

    try:
        data = yf.download(ticker, period="5d", interval="1h", progress=False)
        if data.empty: return None

        # Clean the data for the AI
        current_price = float(data['Close'].iloc[-1].iloc[0] if isinstance(data['Close'].iloc[-1], pd.Series) else data['Close'].iloc[-1])
        open_price = float(data['Open'].iloc[-1].iloc[0] if isinstance(data['Open'].iloc[-1], pd.Series) else data['Open'].iloc[-1])
        
        market_info = (
            f"Asset: {pair_input.upper()}\n"
            f"Current Price: {current_price:.4f}\n"
            f"Last 1H Open: {open_price:.4f}\n"
            f"5-Day High: {float(data['High'].max().iloc[0] if isinstance(data['High'].max(), pd.Series) else data['High'].max()):.4f}\n"
            f"5-Day Low: {float(data['Low'].min().iloc[0] if isinstance(data['Low'].min(), pd.Series) else data['Low'].min()):.4f}\n"
        )
        return market_info
    except Exception as e:
        print(f"Data Error: {e}")
        return None

def scan_all_pairs():
    # This now shows the EXACT prices so the user can verify on MT5/TradingView
    summary = []
    
    for ticker in PAIRS:
        try:
            data = yf.download(ticker, period="2d", interval="1h", progress=False)
            if not data.empty:
                # Extract values cleanly
                close_p = float(data['Close'].iloc[-1].iloc[0] if isinstance(data['Close'].iloc[-1], pd.Series) else data['Close'].iloc[-1])
                open_p = float(data['Open'].iloc[-1].iloc[0] if isinstance(data['Open'].iloc[-1], pd.Series) else data['Open'].iloc[-1])
                change_pct = ((close_p - open_p) / open_p) * 100
                
                direction = "🟢 BULL" if change_pct >= 0 else "🔴 BEAR"
                name = "GOLD" if ticker == "GC=F" else ticker.replace("=X", "")
                
                # Add exact data to the summary
                summary.append(f"• {name}: Price {close_p:.4f} | {direction} ({change_pct:.2f}% this hour)")
        except:
            continue
            
    if not summary:
        return "Market data unavailable."
    
    return "\n".join(summary)

def generate_chart(pair_input):
    # This creates a literal image of the chart Buddy is looking at
    if pair_input.upper() == "GOLD": ticker = "GC=F"
    elif "=" not in pair_input and "-" not in pair_input: ticker = f"{pair_input.upper()}=X"
    else: ticker = pair_input.upper()

    try:
        data = yf.download(ticker, period="3d", interval="1h", progress=False)
        if data.empty: return None

        # Fix yfinance MultiIndex issue if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Save chart to a temporary file
        filename = f"/tmp/{ticker}_chart.png"
        
        # Draw Candlesticks
        mpf.plot(data, type='candle', style='charles', title=f"{pair_input.upper()} - 1 Hour Chart",
                 ylabel='Price', volume=False, savefig=filename)
        
        return filename
    except Exception as e:
        print(f"Chart Generation Error: {e}")
        return None
