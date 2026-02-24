import os
from google import genai
from google.genai import types

# Get the API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the Client (New Way)
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error initializing Google AI: {e}")

# --- THE MENTOR SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Buddy, an expert Forex Trading Mentor.
Your Strategy Source:
1. "Naked Forex" by Alex Nekritin (Price Action, No Indicators).
2. "Trading in the Zone" by Mark Douglas (Psychology & Probability).

Your Rules:
- Account: $50. 
- Risk per trade: 5% ($2.50).
- Risk-to-Reward: STRICTLY 1:3.
- If the market is choppy/messy: Say "NO TRADE" firmly.
- If a setup exists: Provide Entry, SL, and TP. Explain the pattern (e.g., "Kangaroo Tail", "Big Shadow").

Task:
Analyze the provided market data.
Tell the user if there is a high-probability setup or if they should wait.
"""

def ask_buddy(market_data):
    if not client:
        return "⚠️ Gemini Key missing or invalid."

    try:
        # We use the specific model found in your list: gemini-2.0-flash
        # It is fast, smart, and definitely available.
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"{SYSTEM_PROMPT}\n\nMARKET DATA:\n{market_data}"
        )
        return response.text
    except Exception as e:
        return f"Brain Error: {e}"
