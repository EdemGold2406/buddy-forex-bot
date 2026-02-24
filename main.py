import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Import the new analyze_chart_image function!
from brain import ask_buddy, chat_with_buddy, analyze_chart_image 
from market import get_market_data, scan_all_pairs, generate_chart
from database import log_trade_to_db
from news import get_high_impact_news, get_session_status

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy 5.0 is awake with Vision!")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- NEW: PHOTO HANDLER ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action(action='typing')
    await update.message.reply_text("👀 Buddy is looking at your chart...")
    
    # Get the highest resolution photo sent
    photo_file = await update.message.photo[-1].get_file()
    image_path = f"/tmp/{photo_file.file_id}.jpg"
    
    # Download the image to the server
    await photo_file.download_to_drive(image_path)
    
    # Get any text the user typed with the photo (Caption)
    caption = update.message.caption or "Analyze this chart based on Naked Forex. Does it look like a good setup?"
    
    # Send to Groq Vision
    analysis = analyze_chart_image(image_path, caption)
    
    # Send the result back and clean up
    await update.message.reply_text(f"🧠 **Buddy's Visual Analysis:**\n\n{analysis}", parse_mode='Markdown')
    if os.path.exists(image_path):
        os.remove(image_path)

# --- AUTOMATED JOBS ---
async def hourly_scan_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    snapshot = scan_all_pairs()
    prompt = f"Market Snapshot:\n{snapshot}\n\nIs there a 1:3 setup? If none, explain why briefly and say NO TRADE."
    analysis = ask_buddy(prompt)
    
    if "NO TRADE" not in analysis.upper():
        keyboard = [[InlineKeyboardButton("✅ I Will Trade This", callback_data='take_trade')],
                    [InlineKeyboardButton("❌ Skip", callback_data='skip_trade')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text=f"🚀 **Hourly Result:**\n\n{analysis}", reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # We will keep sending hourly updates so you know he is awake, but keep it brief.
        await context.bot.send_message(chat_id=chat_id, text=f"⏱️ **Hourly Check:** No valid setups right now. Capital protected.", parse_mode='Markdown')

async def daily_news_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    news = get_high_impact_news()
    session = get_session_status()
    message = f"🌅 **Good Morning CEO.**\n\n{session}\n\n📰 **Forex Factory Red News:**\n{news}\n\n_Protect the $50._"
    await context.bot.send_message(chat_id=chat_id, text=message)

# --- BOT COMMANDS ---
async def start_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(hourly_scan_job, interval=3600, first=10, chat_id=chat_id, name="hourly_scan")
    context.job_queue.run_repeating(daily_news_job, interval=86400, first=5, chat_id=chat_id, name="daily_news")
    await update.message.reply_text("🟢 **AUTOPILOT ENGAGED.**\nBuddy will scan hourly. You can also send him screenshots anytime!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'take_trade':
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ **YOU TOOK THIS TRADE.**\n_Reply with `/log PAIR LONG/SHORT ENTRY SL TP` to save._")
    elif query.data == 'skip_trade':
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **TRADE SKIPPED.** Discipline maintained.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_chat_action(action='typing')
    reply = chat_with_buddy(user_text)
    await update.message.reply_text(f"🧠 **Buddy:**\n{reply}")

async def close_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Update 'Outcome' to WIN or LOSS in your Supabase Dashboard.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /check EURUSD")
    pair = context.args[0].upper()
    await update.message.reply_text(f"Fetching raw data for {pair}...")
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
    
    app.add_handler(CommandHandler("start_auto", start_auto))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("log", log))
    app.add_handler(CommandHandler("close", close_trade))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    # NEW: Tell the bot to listen for photos!
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo)) 
    
    print("✅ Buddy 5.0 is running with Vision...")
    app.run_polling()

if __name__ == '__main__':
    main()
