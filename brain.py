import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the AI
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # We are using the specific model found in your list
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        model = None
        print(f"Error configuring Gemini: {e}")
else:
    model = None

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
- If the market is choppy/messy: Say "NO TRADE" firmly. Teach patience.
- If a setup exists: Provide Entry, SL, and TP. Explain the pattern (e.g., "Kangaroo Tail", "Big Shadow").

Task:
Analyze the provided market data.
Tell the user if there is a high-probability setup or if they should wait.
"""

def ask_buddy(market_data):
    if not model:
        return "⚠️ Gemini Key missing or invalid."

    try:
        # Standard generation call
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nMARKET DATA:\n{market_data}")
        return response.text
    except Exception as e:
        return f"Brain Error: {e}"
