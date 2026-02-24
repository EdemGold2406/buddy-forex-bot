import os
import base64
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """
You are Buddy, an elite Technical Analysis King and SMC Master.
Strategy: Market Structure, Liquidity Sweeps, Order Blocks, and FVG.
Psychology: Probabilistic mindset (Mark Douglas).
Rules: $50 Account. 5% Risk ($2.50). 1:3 R:R.
Output: Analyze Structure, Liquidity, and Price Action. End with GO or NO TRADE.
"""

def chat_with_buddy(user_message):
    if not client: return "⚠️ API Key missing."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
            temperature=0.6, max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Brain Error: {e}"

def analyze_chart_image(image_path, pair_name):
    if not client: return "⚠️ API Key missing."
    
    # We will try these models in order of stability
    models_to_try = ["llama-3.2-90b-vision-preview", "llama-3.2-11b-vision-preview"]
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    last_error = ""
    for model_name in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"{SYSTEM_PROMPT}\n\nTask: Analyze this H1 chart for {pair_name}."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=800
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_error = str(e)
            continue # Try the next model if this one fails
            
    return f"Vision Error (All models failed): {last_error}"
