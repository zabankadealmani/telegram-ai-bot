import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 744748269

USERS_FILE = "users.json"

# 📦 DB
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(data):
    json.dump(data, open(USERS_FILE, "w"))

users = load_users()

# 🧠 STATE
admin_state = {}

# 📚 LINKS (NEW)
LINKS = {
    "edu": "https://t.me/+IcNQUW7bM_xjZjdk",
    "film": "https://t.me/+5Ll-_PHEmfEwOWQ8",
    "podcast": "https://t.me/+a5HK5Ktg1kNiY2E0",
    "job": "https://t.me/+TFAMe1OSiBhmZDhk",
    "music": "https://t.me/+p0_P4lFcvIo0NWI0",
    "exam": "https://t.me/+VMSXWp62w-Q0MGQ8",
    "class": "https://t.me/+Gq6nK-16B7Y2OTk0",
    "support": "https://t.me/ketabun"
}

# 📚 MENU
def main_menu():
    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton("📚 آموزش زبان", url=LINKS["edu"]),
            InlineKeyboardButton("🎬 فیلم آلمانی", url=LINKS["film"])
        ],

        [
            InlineKeyboardButton("🎧 پادکست", url=LINKS["podcast"]),
            InlineKeyboardButton("🎵 آهنگ", url=LINKS["music"])
        ],

        [
            InlineKeyboardButton("💼 اوسبیلدونگ", url=LINKS["job"]),
            InlineKeyboardButton("🧪 آزمون", url=LINKS["exam"])
        ],

        [
            InlineKeyboardButton("🎓 کلاس رایگان", url=LINKS["class"]),
            InlineKeyboardButton("🆘 پشتیبانی", url=LINKS["support"])
        ],

        [
            InlineKeyboardButton("📊 تعیین سطح", callback_data="level"),
            InlineKeyboardButton("🧠 ترجمه", callback_data="translate")
        ]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    users[uid] = {
        "name": update.effective_user.first_name
    }
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی!\n\n💡 یک کلمه یا جمله بفرست تا ترجمه کنم",
        reply_markup=main_menu()
    )

# 📩 FORWARD TO ADMIN
async def forward_to_admin(update: Update):

    user = update.effective_user
    text = update.message.text

    msg = f"""
📩 پیام جدید

👤 {user.first_name}
🆔 {user.id}

💬 {text}
"""

    await update.get_bot().send_message(
        chat_id=ADMIN_ID,
        text=msg
    )

# 🤖 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await forward_to_admin(update)

    text = update.message.text

    await update.message.reply_text(
        "🧠 ترجمه:\n" + text,
        reply_markup=main_menu()
    )

# 🛠 ADMIN STATE
admin_state = {}

# 🛠 CALLBACKS
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "translate":
        await query.message.reply_text("💬 فقط پیام بفرست تا ترجمه کنم")

# 🚀 RUN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
