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
user_test = {}

# 🔗 LINKS
LINKS = {
    "support": "https://t.me/ketabun",
    "edu": "https://t.me/+IcNQUW7bM_xjZjdk",
    "class": "https://t.me/+Gq6nK-16B7Y2OTk0",
    "film": "https://t.me/+5Ll-_PHEmfEwOWQ8",
    "podcast": "https://t.me/+a5HK5Ktg1kNiY2E0",
    "music": "https://t.me/+p0_P4lFcvIo0NWI0",
    "job": "https://t.me/+TFAMe1OSiBhmZDhk",
    "exam": "https://t.me/+VMSXWp62w-Q0MGQ8"
}

# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton("🆘 پشتیبانی", url=LINKS["support"])
        ],

        [
            InlineKeyboardButton("📚 آموزش", url=LINKS["edu"])
        ],

        [
            InlineKeyboardButton("🎓 کلاس آنلاین", url=LINKS["class"])
        ],

        [
            InlineKeyboardButton("🎬 فیلم", url=LINKS["film"]),
            InlineKeyboardButton("🎧 پادکست", url=LINKS["podcast"])
        ],

        [
            InlineKeyboardButton("🎵 موزیک", url=LINKS["music"]),
            InlineKeyboardButton("💼 اوسبیلدونگ", url=LINKS["job"])
        ],

        [
            InlineKeyboardButton("🧪 آزمون", url=LINKS["exam"]),
            InlineKeyboardButton("📊 تعیین سطح", callback_data="start_test")
        ]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    users[uid] = {"name": update.effective_user.first_name, "level": None}
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی 🇩🇪\n\n"
        "💡 یک کلمه یا جمله بفرست تا ترجمه کنم\n\n"
        "📊 یا در تعیین سطح شرکت کن تا مسیرت مشخص بشه",
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

    await update.get_bot().send_message(chat_id=ADMIN_ID, text=msg)

# 🤖 TRANSLATION MODE
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await forward_to_admin(update)

    await update.message.reply_text(
        "🧠 ترجمه:\n" + update.message.text,
        reply_markup=main_menu()
    )

# 📊 LEVEL TEST SYSTEM
LEVELS = ["A1", "A2", "B1", "B2"]

QUESTIONS = {
    "A1": [
        {"q": "Haus یعنی چی؟", "a": "B"},
        {"q": "Buch یعنی چی؟", "a": "B"},
        {"q": "Hallo یعنی چی؟", "a": "B"},
    ],
    "A2": [
        {"q": "Ich bin müde یعنی چی؟", "a": "A"},
        {"q": "Er geht zur Schule یعنی چی؟", "a": "B"},
    ],
    "B1": [
        {"q": "weil یعنی چی؟", "a": "چون"},
    ],
    "B2": [
        {"q": "ترجمه: اگر وقت داشتم می‌آمدم", "a": "Wenn ich Zeit hätte, würde ich kommen"},
    ]
}

# 🎯 START TEST
async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    user_test[uid] = {
        "level_index": 0,
        "step": 0,
        "correct": 0,
        "wrong": 0
    }

    await send_question(update, context)

# ❓ SEND QUESTION
async def send_question(update, context):

    uid = update.effective_user.id
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

# 🔙 BACK BUTTON
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🏠 برگشتی به منوی اصلی",
        reply_markup=main_menu()
    )

# 📊 CHECK ANSWER
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    state = user_test[uid]

    answer = query.data
    correct = state["current"]["a"]

    if answer == correct:
        state["correct"] += 1
    else:
        state["wrong"] += 1

    state["step"] += 1

    # 🎯 END TEST
    if state["step"] >= 10:

        level = LEVELS[state["level_index"]]

        if state["correct"] >= 8:
            if state["level_index"] < 3:
                final_level = LEVELS[state["level_index"] + 1]
            else:
                final_level = "B2"
        else:
            final_level = level

        users[str(uid)]["level"] = final_level
        save_users(users)

        del user_test[uid]

        await query.message.reply_text(
            f"📊 نتیجه آزمون:\n🎯 سطح شما: {final_level}",
            reply_markup=main_menu()
        )
        return

    # ⬆ difficulty jump
    if state["step"] % 3 == 0 and state["correct"] >= 2:
        if state["level_index"] < 3:
            state["level_index"] += 1

    await send_question_from_callback(query, context)

# ❓ NEXT QUESTION
async def send_question_from_callback(query, context):

    uid = query.from_user.id
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

    await query.message.reply_text(q["q"], reply_markup=keyboard)

# 🧠 CALLBACK ROUTER
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "start_test":
        await start_test(update, context)

    elif query.data == "back":
        await handle_back(update, context)

    else:
        await check_answer(update, context)

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
