import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 کلیدها
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269

USERS_FILE = "users.json"

# 👥 ذخیره کاربران حرفه‌ای
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(users):
    json.dump(users, open(USERS_FILE, "w"))

users = load_users()

# 📊 وضعیت تعیین سطح
user_state = {}

# 📚 سوالات تعیین سطح
QUESTIONS = [
    {"q": "Haus یعنی چی؟", "options": ["A) ماشین", "B) خانه", "C) کتاب", "D) میز"], "answer": "B"},
    {"q": "der Tisch یعنی چی؟", "options": ["A) میز", "B) در", "C) پنجره", "D) دیوار"], "answer": "A"},
    {"q": "Hallo یعنی چی؟", "options": ["A) خداحافظ", "B) سلام", "C) ممنون", "D) ببخشید"], "answer": "B"},
    {"q": "Buch یعنی چی؟", "options": ["A) کتاب", "B) خانه", "C) ماشین", "D) آب"], "answer": "A"},
    {"q": "Ich bin müde یعنی چی؟", "options": ["A) خوشحالم", "B) خسته‌ام", "C) می‌روم", "D) می‌خورم"], "answer": "B"},
]

# 🟢 منوی اصلی
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 کلاس آنلاین رایگان", url="https://t.me/+Gq6nK-16B7Y2OTk0")],
        [InlineKeyboardButton("📊 تعیین سطح", callback_data="level")],
        [InlineKeyboardButton("🆘 پشتیبانی", url="https://t.me/ketabun")]
    ])

# 🔙 منوی بازگشت
def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="home")]
    ])

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users[str(user.id)] = {
        "username": user.username,
        "first_name": user.first_name,
        "joined": str(datetime.now())
    }

    save_users(users)

    await update.message.reply_text(
        "👋 به ربات زبانساز خوش آمدی 🇩🇪\n\n"
        "📌 امکانات:\n"
        "✔ ترجمه فارسی ↔ آلمانی\n"
        "✔ دیکشنری هوشمند\n"
        "✔ تعیین سطح واقعی\n\n"
        "💡 فقط یک کلمه یا جمله بفرست تا ترجمه کنم",
        reply_markup=main_menu()
    )

# 📊 شروع تعیین سطح (فوری بدون مشکل)
async def start_level(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    user_state[user_id] = {"step": 0, "score": 0}

    q = QUESTIONS[0]

    await query.message.reply_text(
        "📊 تعیین سطح شروع شد 🇩🇪\n\n"
        + q["q"] + "\n" + "\n".join(q["options"])
    )

# ⚙️ دکمه‌ها
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    # 📊 شروع تعیین سطح
    if query.data == "level":
        await start_level(update, context)
        return

    # 🔙 برگشت به منو
    if query.data == "home":
        await query.edit_message_text(
            "👋 منوی اصلی",
            reply_markup=main_menu()
        )
        return

# 🧠 پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.effective_user.id

    # 📊 اگر در تعیین سطح هست
    if user_id in user_state:

        state = user_state[user_id]
        q = QUESTIONS[state["step"]]

        if text.strip().upper() == q["answer"]:
            state["score"] += 1

        state["step"] += 1

        # پایان آزمون
        if state["step"] >= len(QUESTIONS):

            score = state["score"]
            del user_state[user_id]

            if score >= 4:
                level = "A2 🟡"
                book = "Starten Wir"
            else:
                level = "A1 🟢"
                book = "Starten Wir"

            await update.message.reply_text(
                f"📊 نتیجه تعیین سطح:\n\n"
                f"سطح شما: {level}\n"
                f"📚 کتاب پیشنهادی: {book}\n",
                reply_markup=back_menu()
            )
            return

        next_q = QUESTIONS[state["step"]]

        await update.message.reply_text(
            next_q["q"] + "\n" + "\n".join(next_q["options"])
        )
        return

    # 🚫 غیر مرتبط
    if any(x in text.lower() for x in ["فیلم", "بازی", "اخبار"]):
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

    # 🤖 ترجمه هوشمند
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
کوتاه جواب بده (حداکثر 2 خط)
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
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
