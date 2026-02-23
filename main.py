import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from brain import ask_buddy
from market import get_market_data
from database import log_trade_to_db

# Load Telegram Token from Render Environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi, I am Buddy!\n\n"
        "I am your business partner for Forex.\n"
        "Commands:\n"
        "/check EURUSD - Scan for 1:3 setups\n"
        "/log EURUSD LONG 1.05 1.04 1.08 - Journal a trade"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check PAIR (e.g., /check GBPJPY)")
        return
    
    pair = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {pair}...")
    
    # 1. Get Data
    market_info = get_market_data(pair)
    if not market_info:
        await update.message.reply_text("❌ Could not fetch data.")
        return

    # 2. Ask AI
    analysis = ask_buddy(market_info)
    
    await update.message.reply_text(f"📊 **Buddy's Analysis:**\n\n{analysis}", parse_mode='Markdown')

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Expected: /log PAIR DIR ENTRY SL TP
        pair = context.args[0].upper()
        direction = context.args[1].upper()
        entry = float(context.args[2])
        sl = float(context.args[3])
        tp = float(context.args[4])
        
        # 5% of $50 = $2.50
        risk = 2.50 
        
        success = log_trade_to_db(pair, direction, entry, sl, tp, risk)
        if success:
            await update.message.reply_text(f"✅ Trade saved to Supabase!\nRisk: ${risk}")
        else:
            await update.message.reply_text("❌ Database Error.")
            
    except IndexError:
        await update.message.reply_text("❌ Format: /log EURUSD LONG 1.1000 1.0950 1.1150")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: No TELEGRAM_TOKEN found.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("log", log))
    
    print("✅ Buddy is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
