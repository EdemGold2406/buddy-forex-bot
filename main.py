import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from brain import ask_buddy
from market import get_market_data, scan_all_pairs, generate_chart # Added generate_chart
from database import log_trade_to_db

# ==========================================
# 1. FAKE WEB SERVER
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy is Alive with Visual Charts!")

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
        "👋 **Buddy (Transparent Edition)**\n"
        "I now provide visual proof of my analysis.\n\n"
        "Commands:\n"
        "/scan - View EXACT prices & momentum of the Big 5.\n"
        "/check EURUSD - Get the Chart Image + Analysis.\n"
        "/log EURUSD LONG 1.05 1.04 1.08 - Journal Trade."
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👀 Checking live interbank prices...")
    
    # 1. Show the user EXACTLY what data Buddy is looking at
    snapshot = scan_all_pairs()
    await update.message.reply_text(f"📊 **Raw Market Data:**\n{snapshot}\n\n*Sending this to Llama 3 for analysis...*")
    
    # 2. Get AI Analysis
    prompt = f"Market Data:\n{snapshot}\n\nBased on Naked Forex, give a brief summary of the market state. Which ONE pair looks most promising for a 1:3 setup? If none, say NO TRADE."
    analysis = ask_buddy(prompt)
    
    await update.message.reply_text(f"🚀 **Buddy's Conclusion:**\n\n{analysis}", parse_mode='Markdown')

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check EURUSD")
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"📸 Taking a snapshot of the {pair} chart...")

    # 1. Generate and send the Chart Image
    chart_file = generate_chart(pair)
    if chart_file and os.path.exists(chart_file):
        with open(chart_file, 'rb') as photo:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
        os.remove(chart_file) # Clean up file to save server space
    else:
        await update.message.reply_text("⚠️ Could not generate chart image, but proceeding with analysis...")

    # 2. Get the Data and Analysis
    data = get_market_data(pair)
    if data:
        analysis = ask_buddy(data)
        await update.message.reply_text(f"🧠 **Buddy's Analysis:**\n\n{analysis}", parse_mode='Markdown')
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

    threading.Thread(target=run_fake_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("log", log))
    
    print("✅ Buddy is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
