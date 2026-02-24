import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from brain import chat_with_buddy, analyze_chart_image

# --- FAKE WEB SERVER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buddy 7.1 TA Beast is awake!")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# The sequence of pairs Buddy wants to check
PAIRS_SEQUENCE = ["EURUSD", "GBPJPY", "USDJPY", "AUDUSD", "XAUUSD (Gold)"]

# ==========================================
# AUTOMATED JOBS
# ==========================================
async def hourly_prompt_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    # Reset the sequence to the first pair
    context.bot_data[chat_id] = 0 
    pair_to_ask = PAIRS_SEQUENCE[0]
    msg = f"⏰ **Hourly TA Session!**\n\nPlease send me the H1 chart screenshot for **{pair_to_ask}**."
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')

# ==========================================
# BOT HANDLERS
# ==========================================
async def start_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(hourly_prompt_job, interval=3600, first=5, chat_id=chat_id, name="hourly_prompt")
    await update.message.reply_text("🟢 **TA Beast Autopilot Active.**\nI will ping you every hour to review the charts one by one.")

async def stop_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_jobs = context.job_queue.get_jobs_by_name("hourly_prompt")
    if not current_jobs:
        await update.message.reply_text("⚠️ Autopilot is already off.")
        return
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("🛑 **Autopilot Paused.**\nType /start_auto to resume.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_index = context.bot_data.get(chat_id, 0)
    
    if current_index >= len(PAIRS_SEQUENCE):
        expected_pair = "General Chart"
    else:
        expected_pair = PAIRS_SEQUENCE[current_index]

    await update.message.reply_chat_action(action='typing')
    await update.message.reply_text(f"👀 Analyzing structure for **{expected_pair}**...", parse_mode='Markdown')
    
    image_path = f"/tmp/chart_{update.effective_user.id}.jpg"
    
    try:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        else:
            return

        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive(image_path)
        
        analysis = analyze_chart_image(image_path, expected_pair)
        await update.message.reply_text(f"🧠 **Buddy's TA ({expected_pair}):**\n\n{analysis}")
        
        # Advance the sequence
        if expected_pair != "General Chart":
            next_index = current_index + 1
            if next_index < len(PAIRS_SEQUENCE):
                context.bot_data[chat_id] = next_index
                next_pair = PAIRS_SEQUENCE[next_index]
                await update.message.reply_text(f"➡️ Send me the H1 chart for **{next_pair}**.", parse_mode='Markdown')
            else:
                context.bot_data[chat_id] = len(PAIRS_SEQUENCE)
                await update.message.reply_text("✅ **All pairs analyzed.** Next session in 1 hour.")
                
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_chat_action(action='typing')
    reply = chat_with_buddy(user_text)
    await update.message.reply_text(f"🧠 Buddy:\n{reply}")

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start_auto", start_auto))
    app.add_handler(CommandHandler("stop_auto", stop_auto))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    print("✅ Buddy 7.1 is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
