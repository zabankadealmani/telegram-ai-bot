import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

# 🔐 FORCE JOIN CHANNEL (YOUR LINK)
CHANNEL_LINK = "https://t.me/+JZRkw2YnlpRlMTM0"

client = OpenAI(api_key=OPENAI_API_KEY)

USERS_FILE = "users.json"

# 📦 USERS DB
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(data):
    json.dump(data, open(USERS_FILE, "w"))

users = load_users()

# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی Ketabun", url="https://t.me/Ketabun"),
            InlineKeyboardButton("📚 آموزش آلمانی", url="https://t.me/+IcNQUW7bM_xjZjdk")
        ],
        [
            InlineKeyboardButton("🎥 کلاس آنلاین", url="https://t.me/+VMSXWp62w-Q0MGQ8"),
            InlineKeyboardButton("🎬 فیلم آلمانی", url="https://t.me/+5Ll-_PHEmfEwOWQ8")
        ],
        [
            InlineKeyboardButton("🎧 پادکست", url="https://t.me/+a5HK5Ktg1kNiY2E0"),
            InlineKeyboardButton("🎵 آهنگ", url="https://t.me/+p0_P4lFcvIo0NWI0")
        ],
        [
            InlineKeyboardButton("🎓 اوسبیلدونگ", url="https://t.me/+TFAMe1OSiBhmZDhk"),
            InlineKeyboardButton("🧪 آزمون سفارت", url="https://t.me/+VMSXWp62w-Q0MGQ8")
        ]
    ])

# 🔐 FORCE JOIN BUTTON
def join_keyboard():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🇩🇪 خوش آمدی به ربات آلمانی\n\n✍️ کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 🤖 AI TRANSLATION (FIXED FORMAT)
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
You are German dictionary bot.

Return EXACT format:

German:
Article:
Plural:
Pronunciation (Persian):
Example:

NO extra text.

WORD: {text}
"""
        }]
    )

    return res.choices[0].message.content

# 📘 EXAMPLE
def ai_example(word):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Make 1 simple German sentence + Persian meaning: {word}"
        }]
    )

    return res.choices[0].message.content

# 🔐 FORCE JOIN CHECK (SIMPLE SAFE VERSION)
user_allowed = set()

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # ❌ NOT JOINED → BLOCK
    if user_id not in user_allowed:

        await update.message.reply_text(
            "❌ برای استفاده باید عضو کانال بشی",
            reply_markup=join_keyboard()
        )
        return

    text = update.message.text
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

# 🔁 CALLBACK ROUTER
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # 🔐 JOIN CHECK
    if data == "check_join":

        user_allowed.add(query.from_user.id)
        await query.message.reply_text("✅ دسترسی فعال شد، حالا استفاده کن")

    # 📘 EXAMPLE
    elif data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(f"📘 مثال:\n\n{ex}")

    # 🔙 BACK
    elif data == "back":
        await query.message.reply_text("🏠 منو اصلی:", reply_markup=main_menu())

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
