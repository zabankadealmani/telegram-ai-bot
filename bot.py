import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 KEYS
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

client = OpenAI(api_key=OPENAI_API_KEY)

USERS_FILE = "users.json"

# 📦 DB
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(data):
    json.dump(data, open(USERS_FILE, "w"))

users = load_users()
user_test = {}
last_word = {}

# 🎓 LINKS
AUSBILDUNG_LINK = "https://t.me/+TFAMe1OSiBhmZDhk"

# 🧭 MAIN MENU
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 پشتیبانی و ثبت‌نام", callback_data="support")],

        [InlineKeyboardButton("📚 آموزش آلمانی", callback_data="edu")],
        [InlineKeyboardButton("🎥 کلاس آنلاین رایگان", callback_data="live")],

        [
            InlineKeyboardButton("🎬 فیلم", callback_data="film"),
            InlineKeyboardButton("🎧 پادکست", callback_data="podcast")
        ],

        [
            InlineKeyboardButton("🎵 آهنگ", callback_data="music"),
            InlineKeyboardButton("🎓 اوسبیلدونگ", callback_data="ausbildung")
        ],

        [
            InlineKeyboardButton("🧪 آمادگی آزمون", callback_data="exam"),
            InlineKeyboardButton("📊 تعیین سطح", callback_data="start_test")
        ],

        [InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    users[uid] = {
        "name": update.effective_user.first_name,
        "level": None
    }
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی 🇩🇪\n\n"
        "✍️ هر چیزی بفرستی ترجمه می‌کنم (فارسی ↔ آلمانی)\n"
        "📘 آرتیکل + جمع + مثال (با دکمه)",
        reply_markup=main_menu()
    )

# 🤖 AI TRANSLATION
def ai_translate(text):

    prompt = f"""
Translate Persian ↔ German.

Text: {text}

Return:
1. Translation
2. Article (if noun)
3. Plural (if noun)

NO example sentence.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Persian-German teacher."},
            {"role": "user", "content": prompt}
        ]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    text = update.message.text

    # 📩 send to admin
    await context.bot.send_message(
        ADMIN_ID,
        f"📩 پیام کاربر {uid}:\n{text}"
    )

    result = ai_translate(text)
    last_word[uid] = text

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📘 مثال", callback_data="example"),
            InlineKeyboardButton("🔙 برگشت", callback_data="home")
        ]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

# 📊 SMART TEST
LEVELS = ["A1", "A2", "B1", "B2"]

QUESTIONS = {
    "A1": [
        {"q": "Haus یعنی چی؟", "a": "خانه"},
        {"q": "Buch یعنی چی؟", "a": "کتاب"},
    ],
    "A2": [
        {"q": "Ich bin müde یعنی چی؟", "a": "من خسته هستم"},
    ],
    "B1": [
        {"q": "weil یعنی چی؟", "a": "چون"},
    ],
    "B2": [
        {"q": "Wenn ich Zeit hätte...", "a": "اگر وقت داشتم می‌آمدم"},
    ]
}

# 🎯 START TEST
async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    user_test[uid] = {
        "level_index": 0,
        "step": 0,
        "correct": 0
    }

    await send_question(query)

# ❓ QUESTION
async def send_question(update):

    uid = update.from_user.id
    state = user_test[uid]

    level = LEVELS[state["level_index"]]
    q = random.choice(QUESTIONS[level])

    state["current"] = q

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
    ])

    await update.message.reply_text(q["q"], reply_markup=keyboard)

# 📊 CHECK ANSWER
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    state = user_test.get(uid)

    if not state:
        return

    user_answer = update.message.text.strip().lower()
    correct = state["current"]["a"].lower()

    if user_answer == correct:
        state["correct"] += 1

    state["step"] += 1

    if state["step"] >= 10:

        if state["correct"] >= 8:
            new_level = LEVELS[min(state["level_index"] + 1, 3)]
        else:
            new_level = LEVELS[state["level_index"]]

        users[str(uid)]["level"] = new_level
        save_users(users)

        del user_test[uid]

        await update.message.reply_text(
            f"📊 سطح شما: {new_level}",
            reply_markup=main_menu()
        )
        return

    await send_question(update)

# 🔁 CALLBACK HANDLER
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # 🏠 HOME
    if data == "home":
        await query.message.reply_text("🏠 منو:", reply_markup=main_menu())

    # 📘 EXAMPLE
    elif data == "example":
        await query.message.reply_text(
            f"💡 مثال:\nDas {last_word.get(str(query.from_user.id), '')} ist gut.\n→ مثال ساخته شد"
        )

    # 🎓 AUSBILDUNG
    elif data == "ausbildung":
        await query.message.reply_text(f"🎓 اوسبیلدونگ:\n{AUSBILDUNG_LINK}")

    # ⚙️ ADMIN PANEL
    elif data == "admin":
        if query.from_user.id == ADMIN_ID:
            await query.message.reply_text(admin_stats())
        else:
            await query.message.reply_text("❌ دسترسی ندارید")

    # 📊 TEST START
    elif data == "start_test":
        await start_test(update, context)

    else:
        await check_answer(update, context)

# 📊 ADMIN STATS
def admin_stats():

    total = len(users)
    levels = {"A1":0,"A2":0,"B1":0,"B2":0}

    for u in users.values():
        lvl = u.get("level")
        if lvl in levels:
            levels[lvl] += 1

    return f"""
📊 آمار ربات:

👥 کاربران: {total}

🟢 A1: {levels['A1']}
🟡 A2: {levels['A2']}
🟠 B1: {levels['B1']}
🔴 B2: {levels['B2']}
"""

# 🚀 RUN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
