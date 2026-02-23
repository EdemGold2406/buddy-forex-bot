import yfinance as yf
import pandas as pd

def get_market_data(pair):
    ticker = f"{pair}=X"
    try:
        # Fetch 1-hour data for the last 5 days
        data = yf.download(ticker, period="5d", interval="1h", progress=False)
        
        if data.empty:
            return None

        # Clean data structure
        current_price = data['Close'].iloc[-1]
        
        # Calculate Simple Moving Average (SMA)
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
        trend = "BULLISH" if current_price > sma_50 else "BEARISH"

        summary = (
            f"Pair: {pair}\n"
            f"Current Price: {current_price:.5f}\n"
            f"Trend (50 SMA): {trend}\n"
            f"Highest (5d): {data['High'].max():.5f}\n"
            f"Lowest (5d): {data['Low'].min():.5f}\n"
        )
        return summary
    except Exception as e:
        return f"Error fetching data: {e}"
