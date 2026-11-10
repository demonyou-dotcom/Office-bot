from datetime import datetime
import os
from flask import Flask
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Flask server to keep Render happy (keep-alive)
app = Flask(__name__)


@app.route("/")
def home():
    return "Office-bot is alive!"


# Telegram Bot Token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Timezone setup (Cambodia local time)
LOCAL_TZ = pytz.timezone("Asia/Phnom_Penh")

# Dictionary to track start times of breaks for each user
# Format: {user_id: {"activity": "eat", "start_time": datetime_obj}}
user_breaks = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🟢 Startwork", callback_data="startwork"),
            InlineKeyboardButton("🔴 Offwork", callback_data="offwork"),
        ],
        [
            InlineKeyboardButton("🍽️ Eat (40m)", callback_data="eat"),
            InlineKeyboardButton("🚬 Smoke (10m)", callback_data="smoke"),
        ],
        [InlineKeyboardButton("🚻 Toilet (15m)", callback_data="toilet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "Select Office Activity:", reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "Select Office Activity:", reply_markup=reply_markup
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    name = user.first_name

    now = datetime.now(LOCAL_TZ)
    current_time_str = now.strftime("%I:%M %p")
    current_hour = now.hour
    action = query.data

    if action == "startwork":
        # Startwork after 3:00 PM (15:00) is considered late
        if current_hour >= 15:
            message = f"⚠️ {name}, you are late! Startwork logged at: [{current_time_str}]"
        else:
            message = (
                f"✅ {name}, Startwork successful on time! [{current_time_str}]"
            )
        await query.message.reply_text(message)

    elif action == "offwork":
        # Warning if offwork is given before 3:00 AM (03:00)
        if current_hour < 3:
            message = f"⚠️ {name}, you gave Offwork before 3:00 AM! [{current_time_str}]"
        else:
            message = f"🔴 {name}, Offwork logged successfully! [{current_time_str}]"
        await query.message.reply_text(message)

    elif action in ["eat", "smoke", "toilet"]:
        # If user is already on a break, calculate duration when they click another button or finish/switch
        limit_minutes = {"eat": 40, "smoke": 10, "toilet": 15}[action]
        limit_name = {"eat": "Eat (40m)", "smoke": "Smoke (10m)", "toilet": "Toilet (15m)"}[action]

        if user_id in user_breaks:
            prev_data = user_breaks[user_id]
            prev_start = prev_data["start_time"]
            prev_activity = prev_data["activity"]

            elapsed_minutes = int((now - prev_start).total_seconds() / 60)

            if elapsed_minutes > limit_minutes:
                extra_time = elapsed_minutes - limit_minutes
                await query.message.reply_text(
                    f"⚠️ {name} exceeded the time limit for {prev_activity}! Spent {elapsed_minutes} mins (Allowed: {limit_minutes}m). Overtime: {extra_time} mins."
                )

        # Record
