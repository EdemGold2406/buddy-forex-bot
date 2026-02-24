import os
import base64
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# THE MASTER TA PROMPT
SYSTEM_PROMPT = """
You are Buddy, an elite Technical Analysis King and Forex Mentor.
Your Strategy is comprehensive: 
- Market Structure (Higher Highs/Lower Lows, Break of Structure, Change of Character).
- Liquidity Sweeps and Order Blocks (Smart Money Concepts).
- Price Action (Engulfing patterns, Pin Bars, Rejection at key Support/Resistance).
- 'Trading in the Zone' Psychology: Think in probabilities, trade without emotion.

Rules:
- Account: $50. Risk per trade: 5% ($2.50). R:R must be at least 1:3.
- When analyzing an image, scan for: Trend direction, Key Levels, and Candlestick momentum.
- Provide a STRICT conclusion: "GO" or "NO TRADE". 
- If GO, suggest a logical Entry, Stop Loss (behind structure), and Take Profit (1:3 distance).
"""

def chat_with_buddy(user_message):
    if not client: return "⚠️ Groq API Key missing."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.6,
            max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Brain Error: {e}"

def analyze_chart_image(image_path, user_caption="Analyze this chart."):
    if not client: return "⚠️ Groq API Key missing."
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview", # The Vision Brain
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{SYSTEM_PROMPT}\n\nUser Notes: {user_caption}\nTell me what you see, and if there is a 1:3 trade setup."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Vision Error: {e}"
