import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 کلیدها
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269

USERS_FILE = "users.json"

# 👥 کاربران
def load_users():
    if os.path.exists(USERS_FILE):
        return set(json.load(open(USERS_FILE)))
    return set()

def save_users(users):
    json.dump(list(users), open(USERS_FILE, "w"))

users = load_users()

# 📊 حالت تعیین سطح
user_state = {}

# 📚 سوالات تعیین سطح
QUESTIONS = [
    {"q": "Haus یعنی چی؟", "options": ["A) ماشین", "B) خانه", "C) کتاب", "D) میز"], "answer": "B"},
    {"q": "der Tisch یعنی چی؟", "options": ["A) میز", "B) در", "C) پنجره", "D) دیوار"], "answer": "A"},
    {"q": "Hallo یعنی چی؟", "options": ["A) خداحافظ", "B) سلام", "C) ممنون", "D) ببخشید"], "answer": "B"},
    {"q": "Buch یعنی چی؟", "options": ["A) کتاب", "B) خانه", "C) ماشین", "D) آب"], "answer": "A"},
    {"q": "Ich bin müde یعنی چی؟", "options": ["A) خوشحالم", "B) خسته‌ام", "C) می‌روم", "D) می‌خورم"], "answer": "B"},
    {"q": "Wasser یعنی چی؟", "options": ["A) آب", "B) نان", "C) چای", "D) شیر"], "answer": "A"},
    {"q": "Danke یعنی چی؟", "options": ["A) سلام", "B) خداحافظ", "C) ممنون", "D) لطفاً"], "answer": "C"},
    {"q": "Auto یعنی چی؟", "options": ["A) ماشین", "B) خانه", "C) کتاب", "D) در"], "answer": "A"},
    {"q": "Ich gehe zur Schule یعنی چی؟", "options": ["A) می‌خوابم", "B) به مدرسه می‌روم", "C) می‌خورم", "D) می‌نویسم"], "answer": "B"},
    {"q": "Ich liebe dich یعنی چی؟", "options": ["A) می‌روم", "B) دوستت دارم", "C) می‌خورم", "D) می‌نویسم"], "answer": "B"}
]

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    users.add(user_id)
    save_users(users)

    keyboard = [
        [InlineKeyboardButton("🎓 کلاس آنلاین رایگان", url="https://t.me/+Gq6nK-16B7Y2OTk0")],
        [InlineKeyboardButton("📊 تعیین سطح", callback_data="level")]
    ]

    await update.message.reply_text(
        "👋 به ربات زبانساز خوش آمدی 🇩🇪\n\n"
        "📌 این ربات:\n"
        "✔ ترجمه فارسی ↔ آلمانی\n"
        "✔ دیکشنری هوشمند\n"
        "✔ تعیین سطح زبان\n\n"
        "💡 مثال: اگر مثال خواستی بنویس «مثال میخوام»",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📊 شروع تعیین سطح
async def start_level(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user_state[user_id] = {"step": 0, "score": 0}

    q = QUESTIONS[0]

    await update.message.reply_text(
        "📊 تعیین سطح شروع شد 🇩🇪\n\n"
        + q["q"] + "\n" + "\n".join(q["options"])
    )

# ⚙️ دکمه‌ها
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "level":
        await start_level(update, context)

# 🧠 پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.effective_user.id

    users.add(user_id)
    save_users(users)

    # 📊 تعیین سطح فعال
    if user_id in user_state:

        state = user_state[user_id]
        step = state["step"]

        q = QUESTIONS[step]

        # جواب درست
        if text.startswith(q["answer"]):
            state["score"] += 1

        state["step"] += 1

        # پایان
        if state["step"] >= len(QUESTIONS):

            score = state["score"]
            del user_state[user_id]

            if score >= 8:
                level = "B1 🔵"
                book = "Sicher"
            elif score >= 5:
                level = "A2 🟡"
                book = "Starten Wir"
            else:
                level = "A1 🟢"
                book = "Starten Wir"

            await update.message.reply_text(
                f"📊 نتیجه تعیین سطح:\n\n"
                f"سطح شما: {level}\n"
                f"📚 کتاب پیشنهادی: {book}\n\n"
                "🎓 برای کلاس رایگان وارد کانال شوید"
            )
            return

        next_q = QUESTIONS[state["step"]]

        await update.message.reply_text(
            next_q["q"] + "\n" + "\n".join(next_q["options"])
        )
        return

    # 🚫 غیر مرتبط
    if any(x in text.lower() for x in ["فیلم", "بازی", "سیاسی"]):
        await update.message.reply_text("❌ فقط درباره زبان آلمانی بپرس 🇩🇪")
        return

    # 💡 مثال
    if "مثال" in text:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "یک جمله آلمانی + ترجمه فارسی بده"},
                {"role": "user", "content": "example"}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
        return

    # 🤖 دیکشنری
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو مترجم زبان آلمانی هستی.

فارسی → آلمانی + تلفظ
آلمانی → فارسی
اسم → آرتیکل بده
پاسخ کوتاه
"""
            },
            {"role": "user", "content": text}
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# 🚀 اجرا
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("level", start_level))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
