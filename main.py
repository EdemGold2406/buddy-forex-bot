import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from brain import chat_with_buddy, analyze_chart_image
from database import log_trade_to_db

# --- FAKE WEB SERVER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy 6.1 is awake and watching charts!")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# AUTOMATED JOBS 
# ==========================================
async def hourly_prompt_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    msg = "⏰ **Hourly Check-In!**\nSend me a screenshot from MT5 or TradingView if you see any setups forming. If not, protect the capital."
    await context.bot.send_message(chat_id=chat_id, text=msg)

async def trade_follow_up_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    pair = context.job.data
    msg = f"🔔 **Trade Follow-Up:**\nHey! We logged a trade on {pair} 2 hours ago. How did it play out? (Update your Supabase journal to WIN or LOSS!)"
    await context.bot.send_message(chat_id=chat_id, text=msg)

# ==========================================
# BOT HANDLERS
# ==========================================
async def start_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(hourly_prompt_job, interval=3600, first=10, chat_id=chat_id, name="hourly_prompt")
    await update.message.reply_text("🟢 **Autopilot Active.**\nI will ping you every hour for chart screenshots. Let's hunt!")

# --- THE UPGRADED IMAGE HANDLER ---
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action(action='typing')
    await update.message.reply_text("👀 Buddy is analyzing your chart structure...")
    
    image_path = f"/tmp/chart_{update.effective_user.id}.jpg"
    
    try:
        # Check if sent as Photo or Document
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        else:
            return

        # Download the file
        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive(image_path)
        
        caption = update.message.caption or "Analyze this Forex chart based on Naked Forex rules. Give me Entry, SL, and TP if there is a 1:3 setup."
        
        # Send to Groq Vision
        analysis = analyze_chart_image(image_path, caption)
        
        # Interactive Buttons
        keyboard = [[InlineKeyboardButton("✅ Take Trade", callback_data='take_trade')],
                    [InlineKeyboardButton("❌ No Trade", callback_data='skip_trade')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send without Markdown to prevent crashing
        await update.message.reply_text(f"🧠 Buddy's Analysis:\n\n{analysis}", reply_markup=reply_markup)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing image: {e}")
    finally:
        # Clean up the image from the server
        if os.path.exists(image_path):
            os.remove(image_path)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'take_trade':
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ **Trade Accepted.**\nReply with: `/log PAIR ENTRY SL TP` to journal it.")
    elif query.data == 'skip_trade':
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **Trade Skipped.** Patience is our edge.")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pair, entry, sl, tp = context.args[0].upper(), float(context.args[1]), float(context.args[2]), float(context.args[3])
        direction = "LONG" if tp > entry else "SHORT"
        
        if log_trade_to_db(pair, direction, entry, sl, tp, 2.50):
            await update.message.reply_text(f"✅ Logged {direction} on {pair}!\nI'll check back with you in 2 hours.")
            context.job_queue.run_once(trade_follow_up_job, 7200, chat_id=update.effective_chat.id, data=pair)
        else:
            await update.message.reply_text("❌ Database Error.")
    except:
        await update.message.reply_text("❌ To log, just type: `/log EURUSD 1.100 1.095 1.115`")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_chat_action(action='typing')
    reply = chat_with_buddy(user_text)
    await update.message.reply_text(f"🧠 Buddy:\n{reply}")

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start_auto", start_auto))
    app.add_handler(CommandHandler("log", log))
    
    # UPGRADED: Accepts both normal photos and uncompressed files
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    print("✅ Buddy 6.1 is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
