import os
import logging
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

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

user_status = {}
BD_TIMEZONE = pytz.timezone("Asia/Dhaka")

def get_bd_time():
    return datetime.now(BD_TIMEZONE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 Startwork", callback_data="startwork"), InlineKeyboardButton("🔴 Offwork", callback_data="offwork")],
        [InlineKeyboardButton("🍽️ Eat (40m)", callback_data="eat"), InlineKeyboardButton("🚬 Smoke (10m)", callback_data="smoke")],
        [InlineKeyboardButton("🚻 Toilet (15m)", callback_data="toilet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("অফিস অ্যাক্টিভিটি সিলেক্ট করুন:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_name = query.from_user.first_name
    current_time = get_bd_time()
    action_type = query.data
    current_hour = current_time.hour
    current_minute = current_time.minute

    # 1. STARTWORK: Anytime click, warn if after 3:00 PM (15:00)
    if action_type == "startwork":
        user_status[user_id] = {"active_action": "startwork", "start_time": current_time}
        if current_hour >= 15 and (current_hour > 15 or current_minute > 0):
            await query.message.reply_text(text=f"⚠️ {user_name}, আপনি দেরিতে (দুপুর ৩:টার পরে) Startwork করেছেন! [Time: {current_time.strftime('%I:%M %p')}]")
        else:
            await query.message.reply_text(text=f"✅ {user_name}, সময়মতো Startwork সফল হয়েছে! [Time: {current_time.strftime('%I:%M %p')}]")
        return

    # 2. OFFWORK: Anytime click, warn if before 3:00 AM
    if action_type == "offwork":
        if current_hour < 3:
            await query.message.reply_text(text=f"⚠️ {user_name}, আপনি রাত ৩:টার আগেই Offwork দিয়েছেন! [Time: {current_time.strftime('%I:%M %p')}]")
        else:
            await query.message.reply_text(text=f"🔴 {user_name}, সফলভাবে Offwork রেকর্ড করা হয়েছে। [Time: {current_time.strftime('%I:%M %p')}]")
        
        if user_id in user_status:
            user_status[user_id]["active_action"] = "offwork"
        return

    # 3. BREAKS
    if action_type in ["eat", "smoke", "toilet"]:
        if user_id not in user_status or user_status[user_id].get("active_action") != "startwork":
            await query.message.reply_text(text=f"❌ {user_name}, আগে 'Startwork' করুন তারপর ব্রেক নিতে পারবেন!")
            return

        user_status[user_id][f"{action_type}_start"] = current_time
        await query.message.reply_text(text=f"⏳ {user_name}, আপনার {action_type.capitalize()} শুরু হলো। সময়: {current_time.strftime('%I:%M %p')}")
        return

if __name__ == "__main__":
    keep_alive()
    
    token = "9082371911:AAHrAK-pBBZhreHXXdT-Wu3zxvLx7mNkTrE"
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    
    print("Bot is polling...")
    application.run_polling()
