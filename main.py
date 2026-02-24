import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
# --- FIXED IMPORT BELOW ---
from brain import ask_buddy 
from market import get_market_data, scan_all_pairs
from database import log_trade_to_db

# ==========================================
# 1. FAKE WEB SERVER (For Render Health Check)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy is Alive!")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# 2. BOT LOGIC
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Buddy 2.0 Online**\n"
        "Powered by Gemini 2.0 Flash (Newest Model)\n\n"
        "Commands:\n"
        "/scan - Check 'Big 5' Pairs\n"
        "/check EURUSD - Deep Analysis\n"
        "/log EURUSD LONG 1.05 1.04 1.08 - Journal Trade"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👀 Scanning Big 5 pairs...")
    snapshot = scan_all_pairs()
    prompt = f"Market Snapshot:\n{snapshot}\n\nBased on Naked Forex, which ONE pair is best for a 1:3 setup? If none, say NO TRADE."
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
        await update.message.reply_text(f"📊 **{pair} Analysis:**\n\n{analysis}", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Data Error.")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pair, direction, entry, sl, tp = context.args[0], context.args[1], float(context.args[2]), float(context.args[3]), float(context.args[4])
        if log_trade_to_db(pair, direction, entry, sl, tp, 2.50):
            await update.message.reply_text("✅ Trade Journaled.")
        else:
            await update.message.reply_text("❌ Database Error.")
    except:
        await update.message.reply_text("❌ Usage: /log EURUSD LONG 1.10 1.09 1.13")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: No TELEGRAM_TOKEN found.")
        return

    # Start Fake Server
    threading.Thread(target=run_fake_server, daemon=True).start()

    # Start Bot
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("log", log))
    
    print("✅ Buddy is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
