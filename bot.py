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

# Dictionary to track ongoing breaks for each user
# Format: {user_id: {"activity": "Eat", "limit": 40, "start_time": datetime_obj}}
user_active_breaks = {}


def get_main_keyboard():
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
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Seat", callback_data="back_to_seat")]]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # If user is currently on a break, restrict them to Back to Seat only
    if user_id in user_active_breaks:
        active_activity = user_active_breaks[user_id]["activity"]
        reply_markup = get_back_keyboard()
        text = f"⚠️ You are currently on {active_activity} break! You must click 'Back to Seat' first."
    else:
        reply_markup = get_main_keyboard()
        text = "Select Office Activity:"

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)


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

    # Check if user is currently on a break
    if user_id in user_active_breaks:
        # If they are on a break, they are ONLY allowed to click 'back_to_seat'
        if action != "back_to_seat":
            active_activity = user_active_breaks[user_id]["activity"]
            await query.message.reply_text(
                f"❌ Error, {name}! You are currently on a {active_activity} break. You cannot click other options until you click 'Back to Seat'!",
                reply_markup=get_back_keyboard(),
            )
            return

        # Handling Back to Seat
        break_info = user_active_breaks[user_id]
        activity_name = break_info["activity"]
        limit_minutes = break_info["limit"]
        start_time = break_info["start_time"]

        elapsed_minutes = int((now - start_time).total_seconds() / 60)
        
        # Remove user from active break state
        del user_active_breaks[user_id]

        if elapsed_minutes > limit_minutes:
            extra_time = elapsed_minutes - limit_minutes
            message = f"⚠️ {name} took extra time on {activity_name}! Spent {elapsed_minutes} mins (Allowed: {limit_minutes}m). Overtime: {extra_time} mins. [{current_time_str}]"
        else:
            message = f"✅ {name} returned to seat on time from {activity_name}! Spent {elapsed_minutes} mins. [{current_time_str}]"

        await query.message.reply_text(message, reply_markup=get_main_keyboard())
        return

    # Normal actions when NOT on a break
    if action == "startwork":
        if current_hour >= 15:
            message = f"⚠️ {name}, you are late! Startwork logged at: [{current_time_str}]"
        else:
            message = f"✅ {name}, Startwork successful on time! [{current_time_str}]"
        await query.message.reply_text(message, reply_markup=get_main_keyboard())

    elif action == "offwork":
        if current_hour < 3:
            message = f"⚠️ {name}, you gave Offwork before 3:00 AM! [{current_time_str}]"
        else:
            message = f"🔴 {name}, Offwork logged successfully! [{current_time_str}]"
        await query.message.reply_text(message, reply_markup=get_main_keyboard())

    elif action in ["eat", "smoke", "toilet"]:
        limits = {"eat": (40, "Eat (40m)"), "smoke": (10, "Smoke (10m)"), "toilet": (15, "Toilet (15m)")}
        limit_minutes, limit_name = limits[action]

        # Save break state
        user_active_breaks[user_id] = {
            "activity": limit_name,
            "limit": limit_minutes,
            "start_time": now,
        }

        await query.message.reply_text(
            f"⏱️ {name} started {limit_name} at [{current_time_str}]. Click 'Back to Seat' when you return.",
            reply_markup=get_back_keyboard(),
        )

    else:
        await query.message.reply_text(f"📌 {name}: {action} at [{current_time_str}]", reply_markup=get_main_keyboard())


def main():
    if not TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN provided in environment variables.")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()


if __name__ == "__main__":
    import threading

    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0", port=int(os.environ.get("PORT", 10000))
        )
    ).start()
    main()
