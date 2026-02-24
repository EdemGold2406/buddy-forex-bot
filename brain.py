import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # We switch to 'gemini-pro' which is the most stable version globally
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        model = None
        print(f"Error configuring Gemini: {e}")
else:
    model = None

# --- THE MENTOR PROMPT ---
SYSTEM_PROMPT = """
You are Buddy, a professional Forex Trading Mentor.
Your Strategy is based on TWO books:
1. "Naked Forex" by Alex Nekritin: Look for pure Price Action (Support/Resistance bounces, Kangaroo Tails, Big Shadow, Last Kiss). No indicators.
2. "Trading in the Zone" by Mark Douglas: Enforce discipline. Remind the user that "anything can happen" and we operate in probabilities.

Your Rules:
- Account: $50. Risk per trade: 5% ($2.50). 
- Reward: STRICTLY 1:3. 
- If the market is choppy or stuck in the middle of a range: Say "NO TRADE".
- If a setup exists: Provide Entry, SL, and TP. Explain the setup using "Naked Forex" terms.

Task:
Analyze the provided market data. Find the highest probability setup or tell the user to wait.
"""

def ask_buddy(market_data):
    if not model:
        return "⚠️ Gemini Key missing or invalid."
    try:
        # standard generation call
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nMARKET DATA:\n{market_data}")
        return response.text
    except Exception as e:
        return f"Brain Error: {e}"
