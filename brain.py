import os
from google import genai

# Get API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Client
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error initializing Google AI: {e}")

# --- MENTOR INSTRUCTIONS ---
SYSTEM_PROMPT = """
You are Buddy, an expert Forex Trading Mentor.
Strategy: "Naked Forex" (Price Action) & "Trading in the Zone" (Psychology).
Rules:
- Account: $50. Risk: 5% ($2.50). R:R: 1:3.
- Logic: Look for Pin Bars, Engulfing, Support/Resistance Bounces.
- Output: "GO" or "NO TRADE". If GO, provide Entry, SL, TP.
"""

def ask_buddy(market_data):
    if not client:
        return "⚠️ Gemini Key missing."

    try:
        # Using the specific model available to your key: gemini-2.0-flash
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"{SYSTEM_PROMPT}\n\nMARKET DATA:\n{market_data}"
        )
        return response.text
    except Exception as e:
        return f"Brain Error: {e}"
