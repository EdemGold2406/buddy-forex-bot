import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

SYSTEM_PROMPT = """
You are Buddy, a professional Forex risk manager and mentor.
Your Goal: Protect the user's capital ($50 account, 5% risk, 1:3 R:R).
Philosophy: 'Trading in the Zone' by Mark Douglas.
Task: Analyze the market data provided. 
- If setups are messy/choppy: Say NO. 
- If setup is clear: Say YES, provide Entry, SL, TP (1:3).
- Always include a psychological tip.
"""

def ask_buddy(market_data):
    if not model:
        return "⚠️ Gemini Key missing."
    
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nDATA:\n{market_data}")
        return response.text
    except Exception as e:
        return f"Brain Error: {e}"
