import os
import base64
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """
You are Buddy, an expert Forex Trading Mentor.
Strategy: "Naked Forex" (Price Action. Look for Kangaroo Tails, Big Shadows, Support/Resistance).
Psychology: "Trading in the Zone" (Mark Douglas).
Rules: $50 Account. 5% Risk per trade ($2.50). STRICT 1:3 R:R.
"""

def ask_buddy(market_data):
    # Standard text-based analysis
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

def analyze_chart_image(image_path, user_caption="Analyze this chart based on our Naked Forex strategy."):
    # THIS IS THE NEW VISION FUNCTION
    if not client: return "⚠️ Groq API Key missing."
    
    try:
        # Read the image and encode it so the AI can "see" it
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview", # Groq's dedicated Vision Model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT + "\n\nUser Question: " + (user_caption or "Analyze this chart.")},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]
                }
            ],
            temperature=0.3, # Keep it highly analytical
            max_tokens=800
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Vision Error: {e}"
