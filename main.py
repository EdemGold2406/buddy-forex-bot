import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from brain import ask_buddy
from market import get_market_data, scan_all_pairs
from database import log_trade_to_db

# ==========================================
# 1. THE FAKE WEB SERVER (To Fix Render Error)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy is Alive and Watching the Markets!")

def run_fake_server():
    # Render tells us which port to use via the 'PORT' variable
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌍 Fake Web Server started on port {port}")
    server.serve_forever()

# ==========================================
# 2. BUDDY'S BRAIN & LOGIC
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Buddy Online!**\n\n"
        "I am connected to the markets and the journal.\n"
        "Commands:\n"
        "1. /scan - Check the 'Big 5' pairs for setups.\n"
        "2. /check EURUSD - Deep analysis of one pair.\n"
        "3. /log EURUSD LONG 1.05 1.04 1.06 - Save a trade."
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👀 Scanning the 'Big 5' pairs... This takes about 10 seconds.")
    
    # 1. Get market snapshot
    market_snapshot = scan_all_pairs()
    
    # 2. Ask the AI
    prompt = (
        f"Here is the market right now:\n{market_snapshot}\n\n"
        "Using 'Naked Forex' (Price Action), which ONE pair looks best for a 1:3 setup? "
        "If they all look bad/choppy, say NO TRADE."
    )
    
    analysis = ask_buddy(prompt)
    await update.message.reply_text(f"🚀 **Scanner Result:**\n\n{analysis}", parse_mode='Markdown')

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check EURUSD")
        return
    pair = context.args[0].upper()
    data = get_market_data(pair)
    if data:
        analysis = ask_buddy(data)
        await update.message.reply_text(f"📊 **Analysis for {pair}:**\n\n{analysis}", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Could not get data.")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Format: /log EURUSD LONG 1.05 1.04 1.06
        pair = context.args[0].upper()
        direction = context.args[1].upper()
        entry = float(context.args[2])
        sl = float(context.args[3])
        tp = float(context.args[4])
        
        # Fixed Risk
        risk = 2.50 
        
        if log_trade_to_db(pair, direction, entry, sl, tp, risk):
            await update.message.reply_text(f"✅ **Journal Updated!**\nRisk: ${risk}\nGo get them!")
        else:
            await update.message.reply_text("❌ Database Error.")
            
    except Exception as e:
        await update.message.reply_text("❌ Format error. Try:\n/log EURUSD LONG 1.05 1.04 1.06")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: No TELEGRAM_TOKEN found.")
        return

    # START THE FAKE SERVER FIRST (In the background)
    # This prevents Render from killing the app
    threading.Thread(target=run_fake_server, daemon=True).start()

    # START THE BOT
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("log", log))
    
    print("✅ Buddy is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
