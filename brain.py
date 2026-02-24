import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Default to None
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # We try the standard, fastest free model
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configuring Gemini: {e}")

# --- THE MENTOR SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are Buddy, a professional Forex Trading Mentor.
Strategy: 'Naked Forex' (Price Action) & 'Trading in the Zone' (Psychology).
Rules:
- Account: $50. Risk: 5% ($2.50). R:R: 1:3.
- Logic: Look for Pin Bars, Engulfing, Support/Resistance Bounces.
- Output: "GO" or "NO TRADE". If GO, provide Entry, SL, TP.
"""

def get_available_models():
    """Helper to ask Google what models are allowed"""
    try:
        if not GEMINI_API_KEY: return "No API Key found."
        
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        return "\n".join(available)
    except Exception as e:
        return f"Could not list models: {e}"

def ask_buddy(market_data):
    # 1. Check if Key exists
    if not GEMINI_API_KEY:
        return "⚠️ Gemini Key is missing in Render Environment."

    # 2. Check if Model loaded
    if not model:
        return "⚠️ Gemini Model failed to load."

    try:
        # 3. Try to generate advice
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nMARKET DATA:\n{market_data}")
        return response.text
    except Exception as e:
        # 4. IF IT FAILS: Tell the user why and list available models
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg:
            available_list = get_available_models()
            return (f"⚠️ **Model Error:** The specific model 'gemini-1.5-flash' was not found.\n\n"
                    f"**Here are the models YOUR key can actually use:**\n{available_list}\n\n"
                    "Please tell the developer to update brain.py with one of these names.")
        return f"Brain Error: {e}"
