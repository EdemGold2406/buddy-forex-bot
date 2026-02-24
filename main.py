import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from brain import ask_buddy, chat_with_buddy
from market import get_market_data, scan_all_pairs, generate_chart
from database import log_trade_to_db
from news import get_high_impact_news, get_session_status

# --- FAKE WEB SERVER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy 4.0 is Autonomous!")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- AUTOMATED JOBS ---
async def hourly_scan_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(chat_id=chat_id, text="⏱️ **Hourly Auto-Scan Initiated...**")
    
    snapshot = scan_all_pairs()
    prompt = f"Market Snapshot:\n{snapshot}\n\nIs there a 1:3 setup? If none, explain why briefly and say NO TRADE."
    analysis = ask_buddy(prompt)
    
    # If a trade is found, add interactive buttons!
    if "NO TRADE" not in analysis.upper():
        keyboard = [
            [InlineKeyboardButton("✅ I Will Trade This", callback_data='take_trade')],
            [InlineKeyboardButton("❌ Skip", callback_data='skip_trade')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text=f"🚀 **Hourly Result:**\n\n{analysis}", reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # If no trade, just send the text
        await context.bot.send_message(chat_id=chat_id, text=f"🛡️ **Capital Protected:**\n\n{analysis}", parse_mode='Markdown')

async def daily_news_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    news = get_high_impact_news()
    session = get_session_status()
    message = f"🌅 **Good Morning CEO.**\n\n{session}\n\n📰 **Forex Factory Red News:**\n{news}\n\n_Protect the $50._"
    await context.bot.send_message(chat_id=chat_id, text=message)

# --- BOT COMMANDS ---
async def start_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This turns on the Autopilot!
    chat_id = update.effective_chat.id
    
    # Schedule the Hourly Scan
    context.job_queue.run_repeating(hourly_scan_job, interval=3600, first=10, chat_id=chat_id, name="hourly_scan")
    
    # Schedule Daily News (Runs every 24 hours)
    context.job_queue.run_repeating(daily_news_job, interval=86400, first=5, chat_id=chat_id, name="daily_news")
    
    await update.message.reply_text("🟢 **AUTOPILOT ENGAGED.**\nBuddy will now scan the markets every hour and check Forex Factory news automatically.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This handles the clicks on "Take Trade" or "Skip"
    query = update.callback_query
    await query.answer()
    
    if query.data == 'take_trade':
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ **YOU TOOK THIS TRADE.**\n_Please reply with `/log PAIR LONG/SHORT ENTRY SL TP` to save it to Supabase._")
    elif query.data == 'skip_trade':
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **TRADE SKIPPED.** Discipline maintained.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This allows you to ask general questions!
    user_text = update.message.text
    await update.message.reply_chat_action(action='typing')
    
    reply = chat_with_buddy(user_text)
    await update.message.reply_text(f"🧠 **Buddy:**\n{reply}")

async def close_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Command to update journal when you close a trade
    await update.message.reply_text("To close a trade, go to your Supabase Dashboard and update the 'Outcome' to WIN or LOSS. (In-bot closing feature coming in v5!).")

# (Keep the check, scan, and log commands from before here)
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /check EURUSD")
    pair = context.args[0].upper()
    await update.message.reply_text(f"📸 Taking a snapshot of {pair}...")
    chart = generate_chart(pair)
    if chart and os.path.exists(chart):
        with open(chart, 'rb') as p: await context.bot.send_photo(chat_id=update.effective_chat.id, photo=p)
        os.remove(chart)
    data = get_market_data(pair)
    if data: await update.message.reply_text(f"🧠 {ask_buddy(data)}", parse_mode='Markdown')

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        p, d, e, sl, tp = context.args[0], context.args[1], float(context.args[2]), float(context.args[3]), float(context.args[4])
        if log_trade_to_db(p, d, e, sl, tp, 2.50): await update.message.reply_text("✅ Trade Journaled in Supabase.")
    except:
        await update.message.reply_text("❌ Format: /log EURUSD LONG 1.10 1.09 1.13")

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start_auto", start_auto)) # NEW: Turns on autopilot
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("log", log))
    app.add_handler(CommandHandler("close", close_trade))
    
    app.add_handler(CallbackQueryHandler(button_handler)) # NEW: Handles buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler)) # NEW: Handles Q&A chat
    
    print("✅ Buddy 4.0 is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
