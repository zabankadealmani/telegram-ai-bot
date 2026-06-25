import os
import json
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

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

# 🧠 STATES
user_test = {}

# 🎓 LINKS
LINKS = {
    "support": "https://t.me/YourSupportLink",
    "edu": "https://t.me/+IcNQUW7bM_xjZjdk",
    "live": "https://t.me/+VMSXWp62w-Q0MGQ8",
    "film": "https://t.me/+5Ll-_PHEmfEwOWQ8",
    "podcast": "https://t.me/+a5HK5Ktg1kNiY2E0",
    "music": "https://t.me/+p0_P4lFcvIo0NWI0",
    "ausbildung": "https://t.me/+TFAMe1OSiBhmZDhk",
    "exam": "https://t.me/+VMSXWp62w-Q0MGQ8"
}

# 🧭 MAIN MENU (ALL LINKS)
def main_menu():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 پشتیبانی و ثبت‌نام", url=LINKS["support"])],
        [InlineKeyboardButton("📚 آموزش زبان آلمانی", url=LINKS["edu"])],
        [InlineKeyboardButton("🎥 کلاس آنلاین رایگان", url=LINKS["live"])],
        [InlineKeyboardButton("🎬 فیلم آلمانی", url=LINKS["film"])],
        [InlineKeyboardButton("🎧 پادکست آلمانی", url=LINKS["podcast"])],
        [InlineKeyboardButton("🎵 آهنگ آلمانی", url=LINKS["music"])],
        [InlineKeyboardButton("🎓 اوسبیلدونگ", url=LINKS["ausbildung"])],
        [InlineKeyboardButton("🧪 آمادگی آزمون", url=LINKS["exam"])]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    users[uid] = {"level": "A1"}
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی 🇩🇪\n"
        "✍️ ترجمه + آموزش + آزمون",
        reply_markup=main_menu()
    )

# 🤖 AI TRANSLATION
def ai_translate(text):

    prompt = f"""
Translate Persian ↔ German.

If sentence → full translation
If word → translation + article + plural

NO examples
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "German teacher"},
            {"role": "user", "content": prompt + "\n" + text}
        ]
    )

    return res.choices[0].message.content

# 📘 EXAMPLE AI
def ai_example(word):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Make 1 simple German sentence + Persian meaning"},
            {"role": "user", "content": f"Word: {word}"}
        ]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    text = update.message.text

    # 🚨 TEST MODE
    if uid in user_test:
        await check_answer(update, context)
        return

    # 🤖 TRANSLATION
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

# 🎯 START TEST
async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)

    user_test[uid] = {
        "step": 0,
        "correct": 0,
        "current": None
    }

    await send_question(query)

# ❓ QUESTIONS
QUESTIONS = [
    ("Haus یعنی چی؟", "خانه"),
    ("Buch یعنی چی؟", "کتاب"),
    ("Wasser یعنی چی؟", "آب"),
]

# 📊 SEND QUESTION
async def send_question(update):

    uid = str(update.from_user.id)
    state = user_test[uid]

    q = random.choice(QUESTIONS)
    state["current"] = q

    await update.message.reply_text(
        f"📊 سوال:\n\n{q[0]}\n\n✍️ جواب بده:"
    )

# ✔ CHECK ANSWER
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    if uid not in user_test:
        return

    state = user_test[uid]

    user_answer = update.message.text.strip()
    correct = state["current"][1]

    if user_answer == correct:
        state["correct"] += 1

    state["step"] += 1

    if state["step"] >= 10:

        level = "A2" if state["correct"] >= 8 else "A1"
        users[uid]["level"] = level
        save_users(users)

        del user_test[uid]

        await update.message.reply_text(
            f"📊 سطح شما: {level}",
            reply_markup=main_menu()
        )
        return

    await send_question(update)

# 🔁 CALLBACKS
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":
        await query.message.reply_text("🏠 منو:", reply_markup=main_menu())

    elif data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(f"📘 مثال:\n\n{ex}")

    elif data == "start_test":
        await start_test(update, context)

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
