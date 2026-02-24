import os
from groq import Groq

# Get the key from Render
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the Groq Client
client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Error initializing Groq: {e}")

# --- THE MENTOR SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Buddy, an expert Forex Trading Mentor.
Your Strategy Source:
1. "Naked Forex" by Alex Nekritin (Price Action, No Indicators).
   - Look for: Kangaroo Tails (Pin Bars), Big Shadow (Engulfing), Last Kiss (Breakout & Retest).
2. "Trading in the Zone" by Mark Douglas (Psychology & Probability).

Your Rules:
- Account: $50. 
- Risk per trade: 5% ($2.50).
- Risk-to-Reward: STRICTLY 1:3.
- If the market is choppy/messy: Say "NO TRADE" firmly. Teach patience.
- If a setup exists: Provide Entry, SL, and TP. Explain the pattern.

Task:
Analyze the provided market data.
Tell the user if there is a high-probability setup or if they should wait.
"""

def ask_buddy(market_data):
    if not client:
        return "⚠️ Groq API Key missing. Check Render settings."

    try:
        # We use Llama 3.3 70B (The Smartest Model on your list)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"MARKET DATA:\n{market_data}"}
            ],
            temperature=0.5, # Keep it logical
            max_tokens=1000
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Brain Error: {e}"
