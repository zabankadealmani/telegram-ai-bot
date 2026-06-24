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

user_test = {}

# 🔗 LINKS
LINKS = {
    "edu": "https://t.me/+IcNQUW7bM_xjZjdk",
    "live": "https://t.me/+Gq6nK-16B7Y2OTk0",
    "film": "https://t.me/+5Ll-_PHEmfEwOWQ8",
    "podcast": "https://t.me/+a5HK5Ktg1kNiY2E0",
    "music": "https://t.me/+p0_P4lFcvIo0NWI0",
    "exam": "https://t.me/+VMSXWp62w-Q0MGQ8"
}

# 🧭 MAIN MENU
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 آموزش زبان آلمانی", url=LINKS["edu"])],
        [InlineKeyboardButton("🎥 کلاس آنلاین رایگان", url=LINKS["live"])],
        [
            InlineKeyboardButton("🎬 فیلم", url=LINKS["film"]),
            InlineKeyboardButton("🎧 پادکست", url=LINKS["podcast"])
        ],
        [
            InlineKeyboardButton("🎵 آهنگ", url=LINKS["music"]),
            InlineKeyboardButton("🧪 آمادگی آزمون", url=LINKS["exam"])
        ],
        [
            InlineKeyboardButton("📊 تعیین سطح", callback_data="start_test")
        ]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    users[uid] = {"name": update.effective_user.first_name, "level": None}
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی 🇩🇪\n"
        "✍️ هر کلمه یا جمله بفرستی ترجمه می‌کنم\n"
        "📊 یا در تعیین سطح شرکت کن",
        reply_markup=main_menu()
    )

# 📩 ADMIN FORWARD
async def forward(update: Update):

    u = update.effective_user
    t = update.message.text

    msg = f"📩 {u.first_name} ({u.id})\n💬 {t}"

    await update.get_bot().send_message(ADMIN_ID, msg)

# 🌍 SMART DICTIONARY (WITH ARTICLE + PLURAL)
def translate(text):

    dictionary = {
        "book": {"article": "das", "plural": "die Bücher", "fa": "کتاب"},
        "house": {"article": "das", "plural": "die Häuser", "fa": "خانه"},
        "water": {"article": "das", "plural": "—", "fa": "آب"},
        "hello": {"article": "", "plural": "", "fa": "سلام"},
        "danke": {"article": "", "plural": "", "fa": "ممنون"},
        "ich bin müde": {"article": "", "plural": "", "fa": "من خسته هستم"}
    }

    key = text.lower().strip()

    if key in dictionary:

        item = dictionary[key]

        return (
            f"📘 آرتیکل: {item['article']}\n"
            f"📚 جمع: {item['plural']}\n"
            f"🇮🇷 معنی: {item['fa']}"
        )

    return f"❌ پیدا نشد\n🔎 ترجمه: {text}"

# 💬 MESSAGE HANDLER (NO BUTTONS HERE)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await forward(update)

    result = translate(update.message.text)

    await update.message.reply_text(result)

# 📊 LEVEL TEST SYSTEM
LEVELS = ["A1", "A2", "B1", "B2"]

QUESTIONS = {
    "A1": [
        {"q": "Haus یعنی چی؟", "a": "B"},
        {"q": "Buch یعنی چی؟", "a": "B"},
    ],
    "A2": [
        {"q": "Ich bin müde یعنی چی؟", "a": "A"},
    ],
    "B1": [
        {"q": "weil یعنی چی؟", "a": "چون"},
    ],
    "B2": [
        {"q": "Wenn ich Zeit hätte...", "a": "Wenn ich Zeit hätte, würde ich kommen"},
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
        "correct": 0,
        "wrong": 0
    }

    await send_q(query)

# ❓ QUESTION
async def send_q(update):

    uid = update.from_user.id
    state = user_test[uid]

    level = LEVELS[state["level_index"]]
    q = random.choice(QUESTIONS[level])

    state["current"] = q

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("A", callback_data="A"),
            InlineKeyboardButton("B", callback_data="B"),
            InlineKeyboardButton("C", callback_data="C"),
            InlineKeyboardButton("D", callback_data="D")
        ],
        [
            InlineKeyboardButton("⬅ برگشت", callback_data="back")
        ]
    ])

    await update.message.reply_text(q["q"], reply_markup=keyboard)

# 📊 CHECK ANSWER
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    state = user_test[uid]

    ans = query.data
    correct = state["current"]["a"]

    if ans == correct:
        state["correct"] += 1
    else:
        state["wrong"] += 1

    state["step"] += 1

    if state["step"] >= 10:

        level = LEVELS[state["level_index"]]

        if state["correct"] >= 8:
            final = LEVELS[min(state["level_index"] + 1, 3)]
        else:
            final = level

        users[str(uid)]["level"] = final
        save_users(users)

        del user_test[uid]

        await query.message.reply_text(
            f"📊 سطح شما: {final}",
            reply_markup=main_menu()
        )
        return

    await send_q(query)

# 🔙 BACK BUTTON
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text("🏠 منوی اصلی", reply_markup=main_menu())

# 🧠 ROUTER
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "start_test":
        await start_test(update, context)

    elif query.data == "back":
        await back(update, context)

    else:
        await check(update, context)

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
