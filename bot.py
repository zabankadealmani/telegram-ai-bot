import os
import sqlite3
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from openai import OpenAI


# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

client = OpenAI(api_key=OPENAI_API_KEY)


# 🗄️ DATABASE
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT
)
""")
conn.commit()


# 💾 ALLOWED USERS
ALLOWED_FILE = "allowed.json"
user_allowed = set()

def load_allowed():
    global user_allowed
    if os.path.exists(ALLOWED_FILE):
        with open(ALLOWED_FILE, "r") as f:
            user_allowed = set(json.load(f))

def save_allowed():
    with open(ALLOWED_FILE, "w") as f:
        json.dump(list(user_allowed), f)


# 🔗 JOIN LINK
CHANNEL_LINK = "https://t.me/yourchannel"


# 🧭 MENU
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 کانال", url=CHANNEL_LINK)]
    ])


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 ورود به کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ])


load_allowed()


# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?, ?)",
        (user.id, user.full_name, user.username)
    )
    conn.commit()

    await update.message.reply_text(
        "🇩🇪 ربات آماده است\nکلمه بفرست",
        reply_markup=main_menu()
    )


# 🤖 SAFE AI
def ai_translate(text):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
German word info:
Word: {text}
Return: meaning + example
"""
            }]
        )
        return res.choices[0].message.content
    except:
        return "❌ خطا در دریافت پاسخ از AI"


# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text or ""

    if not text.strip():
        return

    if text.startswith("/"):
        return

    if user.id not in user_allowed:
        await update.message.reply_text(
            "📢 اول عضو کانال شو",
            reply_markup=join_keyboard()
        )
        return

    result = ai_translate(text)

    if not result or not result.strip():
        result = "❌ پاسخ خالی بود"

    await update.message.reply_text(result[:4000])


# 🔁 CALLBACKS
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # join check
    if data == "check_join":
        user_allowed.add(query.from_user.id)
        save_allowed()
        await query.message.reply_text("✅ فعال شد")
        return

    # admin only
    if query.from_user.id == ADMIN_ID:

        if data == "stats":
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            await query.message.reply_text(f"📊 کاربران: {count}")
            return

        if data == "users":
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()

            if not rows:
                await query.message.reply_text("❌ هیچ کاربری نیست")
                return

            text = ""
            for r in rows[:50]:
                text += f"👤 {r[1]} @{r[2] or 'ندارد'}\n🆔 {r[0]}\n\n"

            await query.message.reply_text(text[:4000])
            return

    await query.message.reply_text("⛔ دسترسی ندارید")


# 🚀 MAIN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
