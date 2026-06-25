import os
import json
import sqlite3
import threading
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from openai import OpenAI


# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

client = OpenAI(api_key=OPENAI_API_KEY)


# 🌐 KEEP ALIVE (Render Fix)
app = Flask(__name__)

@app.route("/")
def home():
    return "bot is alive"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run).start()


# 🗄️ SQLITE DB (users)
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


# 💾 PERSIST FAKE JOIN SYSTEM
ALLOWED_FILE = "allowed.json"

def load_allowed():
    global user_allowed
    try:
        with open(ALLOWED_FILE, "r") as f:
            user_allowed = set(json.load(f))
    except:
        user_allowed = set()

def save_allowed():
    with open(ALLOWED_FILE, "w") as f:
        json.dump(list(user_allowed), f)


# 🔐 MEMORY
users_info = {}
user_allowed = set()
users = set()


# 🔗 LINKS
CHANNEL_LINK = "https://t.me/+JZRkw2YnlpRlMTM0"
ONLINE_CLASS_LINK = "https://t.me/+Gq6nK-16B7Y2OTk0"


# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی Ketabun", url="https://t.me/Ketabun"),
            InlineKeyboardButton("📚 آموزش آلمانی", url="https://t.me/+IcNQUW7bM_xjZjdk")
        ],
        [
            InlineKeyboardButton("🎥 کلاس آنلاین رایگان", url=ONLINE_CLASS_LINK),
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


# 🔐 JOIN BUTTON (FAKE BUT STABLE)
def join_keyboard():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 ورود به کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ])


# 👨‍💼 ADMIN PANEL
def admin_panel():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("👥 کاربران", callback_data="users")],
        [InlineKeyboardButton("📢 پیام گروهی", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])


# 🚀 LOAD FAKE ACCESS
load_allowed()


# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users.add(user.id)

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name, username) VALUES (?, ?, ?)",
        (user.id, user.full_name, user.username)
    )
    conn.commit()

    await update.message.reply_text(
        "🇩🇪 خوش آمدی به ربات آلمانی\n✍️ کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )


# 🤖 AI TRANSLATE
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Return EXACT format:

German word
Article + word
Plural
Persian meaning
Persian pronunciation
Example sentence + Persian meaning

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
            "content": f"Give 1 German sentence + Persian meaning: {word}"
        }]
    )

    return res.choices[0].message.content


# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id
    text = update.message.text

    # 🚫 ignore commands
    if text.startswith("/"):
        return

    # 🔐 FAKE GATE (ALWAYS PASS AFTER CLICK)
    if user_id not in user_allowed:

        await update.message.reply_text(
            "📢 ابتدا در کانال زیر عضو شو و سپس روی «عضو شدم» کلیک کن.",
            reply_markup=join_keyboard()
        )
        return

    # 🤖 AI RESPONSE
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text[:20]}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

    # 📩 ADMIN LOG
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=
        f"📩 پیام جدید\n\n"
        f"👤 نام: {user.full_name}\n"
        f"🔹 یوزرنیم: @{user.username if user.username else 'ندارد'}\n"
        f"🆔 آیدی: {user.id}\n\n"
        f"💬 پیام:\n{text}"
    )


# 🔁 CALLBACKS
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ FAKE JOIN (NO REAL CHECK)
    if data == "check_join":

        user_allowed.add(query.from_user.id)
        save_allowed()

        await query.message.reply_text("✅ فعال شد")

    # 📘 EXAMPLE
    elif data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(ex)

    # 🔙 BACK
    elif data == "back":

        await query.message.reply_text("🏠 منو اصلی", reply_markup=main_menu())

    # 👨‍💼 ADMIN
    elif query.from_user.id == ADMIN_ID:

        if data == "stats":

            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]

            await query.message.reply_text(f"📊 کل کاربران: {count}")

        elif data == "users":

            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()

            text = ""

            for r in rows[:50]:

                uid = r[0]
                name = r[1]
                username = r[2] if r[2] else "ندارد"

                text += f"👤 {name}\n🔹 @{username}\n🆔 {uid}\n\n"

            await query.message.reply_text(text[:4000])

        elif data == "broadcast":

            await query.message.reply_text("📢 /broadcast پیام")


# 📢 BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("❌ پیام بنویس")
        return

    cursor.execute("SELECT user_id FROM users")
    all_users = cursor.fetchall()

    sent = 0

    for u in all_users:

        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 {msg}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ ارسال شد به {sent}")


# 🚀 MAIN
def main():

    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("broadcast", broadcast))
    app_bot.add_handler(CommandHandler("admin", lambda u, c: u.message.reply_text("👨‍💼 پنل", reply_markup=admin_panel())))

    app_bot.add_handler(CallbackQueryHandler(router))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app_bot.run_polling()


if __name__ == "__main__":
    main()
