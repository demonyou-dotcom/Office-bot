import os
import logging
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Flask app for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# User status tracking dictionary
user_status = {}

# Bangladesh Timezone (BD Time)
BD_TIMEZONE = pytz.timezone("Asia/Dhaka")

def get_bd_time():
    return datetime.now(BD_TIMEZONE)

# Start command with permanent Reply Keyboard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🟢 Startwork", "🔴 Offwork"],
        ["🍽️ Eat (40m)", "🚬 Smoke (10m)"],
        ["🚻 Toilet (15m)"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)
    await update.message.reply_text("অফিস অ্যাক্টিভিটি সিলেক্ট করুন (নিচের বাটন থেকে):", reply_markup=reply_markup)

# Message handler for button clicks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    current_time = get_bd_time()
    current_hour = current_time.hour
    current_minute = current_time.minute

    # 1. STARTWORK
    if "Startwork" in text:
        user_status[user_id] = {"active_action": "startwork", "start_time": current_time}
        if current_hour >= 15 and (current_hour > 15 or current_minute > 0):
            await update.message.reply_text(text=f"⚠️ {user_name}, আপনি দেরিতে (দুপুর ৩:টার পরে) Startwork করেছেন! [Time: {current_time.strftime('%I:%M %p')}]")
        else:
            await update.message.reply_text(text=f"✅ {user_name}, সময়মতো Startwork সফল হয়েছে! [Time: {current_time.strftime('%I:%M %p')}]")
        return

    # 2. OFFWORK
    if "Offwork" in text:
        if current_hour < 3:
            await update.message.reply_text(text=f"⚠️ {user_name}, আপনি রাত ৩:টার আগেই Offwork দিয়েছেন! [Time: {current_time.strftime('%I:%M %p')}]")
        else:
            await update.message.reply_text(text=f"🔴 {user_name}, সফলভাবে Offwork রেকর্ড করা হয়েছে। [Time: {current_time.strftime('%I:%M %p')}]")
        
        if user_id in user_status:
            user_status[user_id]["active_action"] = "offwork"
        return

    # 3. BREAKS (Eat, Smoke, Toilet)
    if "Eat" in text or "Smoke" in text or "Toilet" in text:
        if user_id not in user_status or user_status[user_id].get("active_action") != "startwork":
            await update.message.reply_text(text=f"❌ {user_name}, আগে 'Startwork' করুন তারপর ব্রেক নিতে পারবেন!")
            return

        action_name = "Eat" if "Eat" in text else ("Smoke" if "Smoke" in text else "Toilet")
        user_status[user_id][f"{action_name.lower()}_start"] = current_time
        await update.message.reply_text(text=f"⏳ {user_name}, আপনার {action_name} শুরু হলো। সময়: {current_time.strftime('%I:%M %p')}")
        return

if __name__ == "__main__":
    keep_alive()
    
    token = "9082371911:AAHrAK-pBBZhreHXXdT-Wu3zxvLx7mNkTrE"
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is polling...")
    application.run_polling()
