from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()

import logging
from datetime import datetime
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# User-der current status track korar jonno dictionary
user_status = {}

# Activities and their durations in seconds
DURATIONS = {
    "eat": 40 * 60,       # 40 minutes
    "smoke": 10 * 60,     # 10 minutes
    "toilet": 15 * 60,    # 15 minutes
    "startwork": 0,
    "offwork": 0
}

# Bangladesh Timezone (BD Time)
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
    await update.message.reply_text("অফিস টাইম শুরু (দুপুর ৩:০০ টা থেকে)। আপনার অ্যাক্টিভিটি সিলেক্ট করুন:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    current_time = get_bd_time()
    action_type = query.data
    duration = DURATIONS.get(action_type, 0)
    
    # Check if work time has started (Bikal 3:00 tar ager check)
    current_hour = current_time.hour
    
    # 3:00 PM mane 15:00 hour
    if current_hour < 15:
        await query.edit_message_text(text=f"⚠️ {user_name}, ekhono dupur ৩:০০ টা বাজে নি! কাজের সময় শুরু হবে দুপুর ৩:০০ টা থেকে।")
        return

    # User er ager kono active kaj ache kina ta check kora
    current_user_data = user_status.get(user_id)
    
    if action_type == "startwork":
        if current_user_data and current_user_data["active_action"] != "offwork":
            active_act = current_user_data["active_action"].upper()
            await query.edit_message_text(text=f"❌ {user_name}, apnar ager kaj ({active_act}) choltese! Age 'Offwork' ba oi kaj sesh korun.")
            return
        
        # Start work successful
        user_status[user_id] = {"active_action": "startwork", "end_time": None}
        await query.edit_message_text(text=f"✅ {user_name} Office **STARTWORK** dilo. (Time: {current_time.strftime('%I:%M %p')})")
        return

    if action_type == "offwork":
        if not current_user_data or current_user_data["active_action"] == "offwork":
            await query.edit_message_text(text=f"⚠️ {user_name}, apni to ekhono kono kajei join korenni ba already offwork e achen!")
            return
        
        # Offwork successful
        user_status[user_id] = {"active_action": "offwork", "end_time": None}
        await query.edit_message_text(text=f"🔴 {user_name} Successfully **OFFWORK** dilo. Ajker moto duty sesh! (Time: {current_time.strftime('%I:%M %p')})")
        return

    # For Eat, Smoke, Toilet checks
    if not current_user_data or current_user_data["active_action"] == "offwork":
        await query.edit_message_text(text=f"⚠️ {user_name}, apni age 'Startwork' দিন, tarpor onno activity (Eat/Smoke/Toilet) e click korun!")
        return

    # Jodi ager kono break-er somoy baki thake
    if "end_time" in current_user_data and current_user_data["end_time"]:
        if current_time.timestamp() < current_user_data["end_time"]:
            remaining_min = int((current_user_data["end_time"] - current_time.timestamp()) / 60)
            await query.edit_message_text(text=f"⚠️ {user_name}, apnar ager break-er somoy ekhono sesh hoyni! Aro {remaining_min} minute baki ache.")
            return

    # Normal Break Entry (Eat, Smoke, Toilet)
    end_timestamp = current_time.timestamp() + duration
    user_status[user_id] = {"active_action": action_type, "end_time": end_timestamp}
    readable_min = int(duration / 60)
    
    await query.edit_message_text(text=f"✅ {user_name} started {action_type.upper()}! Somoy thakbe {readable_min} minute.")

def main():
    TOKEN = "9082371911:AAHrAK-pBBZhreHXXdT-Wu3zxvLx7mNkTrE"
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    import os
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
    
    # Flask keep-alive thread already running above
    # Telegram Bot Application setup
    token = "9082371911:AAHrAK-pBBZhreHXXdT-Wu3zxvLx7mNkTrE"
    application = ApplicationBuilder().token(token).build()
    
    # Handlers add kora
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    
    # Bot run kora (Polling)
    print("Bot is polling...")
    application.run_polling()
