import os
import json
import random
import asyncio
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
broadcast_mode = {}

# 🎓 LINKS
AUSBILDUNG_LINK = "https://t.me/+TFAMe1OSiBhmZDhk"

# 📚 DAILY WORDS
DAILY_WORDS = {
    "A1": ["Haus = خانه", "Buch = کتاب", "Wasser = آب"],
    "A2": ["Ich bin müde = من خسته هستم", "Heute ist schön = امروز خوب است"],
    "B1": ["weil ich keine Zeit habe = چون وقت ندارم"],
    "B2": ["Je mehr ich lerne, desto besser werde ich = هرچی بیشتر یاد بگیرم بهتر میشم"]
}

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
        {"q": "Wenn ich Zeit hätte یعنی چی؟", "a": "اگر وقت داشتم می‌آمدم"},
    ]
}

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
            InlineKeyboardButton("🧪 آزمون", callback_data="start_test"),
            InlineKeyboardButton("📊 تعیین سطح", callback_data="start_test")
        ],

        [InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    users[uid] = {"level": "A1"}
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی 🇩🇪\n"
        "✍️ ترجمه + آموزش + آزمون هوشمند",
        reply_markup=main_menu()
    )

# 🤖 AI TRANSLATE
def ai_translate(text):

    prompt = f"""
Translate Persian ↔ German.

Text: {text}

ONLY:
1. Translation
2. Article
3. Plural
NO example
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "German teacher"},
            {"role": "user", "content": prompt}
        ]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER (FIXED MODE SEPARATION)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    text = update.message.text

    # 📩 send to admin
    await context.bot.send_message(ADMIN_ID, f"📩 {uid}: {text}")

    # 🚨 IF USER IN TEST MODE
    if uid in user_test:
        await check_answer(update, context)
        return

    # 🤖 TRANSLATION MODE
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📘 مثال", callback_data="example"),
            InlineKeyboardButton("🔙 برگشت", callback_data="home")
        ]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

# 🎯 START TEST
async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)

    user_test[uid] = {
        "level_index": 0,
        "step": 0,
        "correct": 0,
        "current": None
    }

    await send_question(query)

# ❓ SEND QUESTION
async def send_question(update):

    uid = str(update.from_user.id)
    state = user_test[uid]

    level = LEVELS[state["level_index"]]
    q = random.choice(QUESTIONS[level])

    state["current"] = q

    await update.message.reply_text(
        f"📊 سوال:\n\n{q['q']}\n\n✍️ جواب را تایپ کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
        ])
    )

# 📊 CHECK ANSWER (FIXED)
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    if uid not in user_test:
        return

    state = user_test[uid]

    user_answer = update.message.text.strip().lower()
    correct = state["current"]["a"].lower()

    if user_answer == correct:
        state["correct"] += 1

    state["step"] += 1

    # 📈 END TEST
    if state["step"] >= 10:

        if state["correct"] >= 8:
            new_level = LEVELS[min(state["level_index"] + 1, 3)]
        else:
            new_level = LEVELS[state["level_index"]]

        users[uid]["level"] = new_level
        save_users(users)

        del user_test[uid]

        await update.message.reply_text(
            f"📊 سطح شما: {new_level}",
            reply_markup=main_menu()
        )
        return

    await send_question(update)

# 🎓 DAILY WORD SYSTEM
async def send_daily_words(app):

    while True:

        for uid, data in users.items():

            try:
                level = data.get("level", "A1")
                words = DAILY_WORDS.get(level, DAILY_WORDS["A1"])
                word = random.choice(words)

                await app.bot.send_message(
                    chat_id=int(uid),
                    text=f"📚 لغت امروز ({level}):\n\n{word}"
                )

            except:
                pass

        await asyncio.sleep(86400)  # 24h

# 📊 ADMIN PANEL
def admin_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 آمار", callback_data="stats")],
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
    ])

# 📊 STATS
def stats():
    total = len(users)
    levels = {"A1":0,"A2":0,"B1":0,"B2":0}

    for u in users.values():
        lvl = u.get("level")
        if lvl in levels:
            levels[lvl] += 1

    return f"""
📊 آمار:

👥 کاربران: {total}

🟢 A1: {levels['A1']}
🟡 A2: {levels['A2']}
🟠 B1: {levels['B1']}
🔴 B2: {levels['B2']}
"""

# 🔁 CALLBACK
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    data = query.data

    if data == "home":
        await query.message.reply_text("🏠 منو:", reply_markup=main_menu())

    elif data == "example":
        await query.message.reply_text("💡 مثال: Das Auto ist schnell.")

    elif data == "ausbildung":
        await query.message.reply_text(f"🎓 اوسبیلدونگ:\n{AUSBILDUNG_LINK}")

    elif data == "admin":
        if query.from_user.id == ADMIN_ID:
            await query.message.reply_text(stats(), reply_markup=admin_panel())
        else:
            await query.message.reply_text("❌ دسترسی ندارید")

    elif data == "stats":
        await query.message.reply_text(stats())

    elif data == "broadcast":
        context.user_data["broadcast"] = True
        await query.message.reply_text("✍️ پیام همگانی را ارسال کنید:")

    elif data == "start_test":
        await start_test(update, context)

# 📢 BROADCAST HANDLER
async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("broadcast"):
        text = update.message.text

        for uid in users.keys():
            try:
                await context.bot.send_message(int(uid), text)
            except:
                pass

        context.user_data["broadcast"] = False
        await update.message.reply_text("✅ ارسال شد")

# 🚀 RUN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message))

    # 🔥 DAILY SYSTEM START
    asyncio.create_task(send_daily_words(app))

    app.run_polling()

if __name__ == "__main__":
    main()
