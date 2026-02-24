import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """
You are Buddy, an expert Forex Trading Mentor.
Strategy: "Naked Forex" (Price Action, No Indicators. Look for Kangaroo Tails, Big Shadows).
Psychology: "Trading in the Zone" (Mark Douglas - Think in probabilities).
Rules: $50 Account. 5% Risk per trade ($2.50). STRICT 1:3 R:R.

When scanning: If market is choppy, say "NO TRADE". If good, give Entry, SL, TP.
When chatting: Answer questions strictly based on Price Action and Mark Douglas psychology. Be concise.
"""

def ask_buddy(market_data):
    if not client: return "⚠️ Groq API Key missing."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"MARKET DATA:\n{market_data}"}
            ],
            temperature=0.4,
            max_tokens=800
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Brain Error: {e}"

def chat_with_buddy(user_message):
    # This handles general questions you ask him
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
