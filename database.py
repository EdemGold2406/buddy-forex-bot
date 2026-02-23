import os
from supabase import create_client, Client

# Fetch keys from Environment Variables (set these in Render later)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase keys missing!")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def log_trade_to_db(pair, direction, entry, sl, tp, risk, status="OPEN"):
    supabase = get_supabase_client()
    if not supabase:
        return "Database Error"
    
    data = {
        "pair": pair,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "risk_amount": risk,
        "status": status
    }
    try:
        supabase.table("trades").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error logging: {e}")
        return False
