import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269

USERS_FILE = "users.json"

# 👥 کاربران
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(users):
    json.dump(users, open(USERS_FILE, "w"))

users = load_users()

# 🧠 حالت کاربران
user_state = {}

# 📊 بانک سوالات حرفه‌ای (بدون تکرار + 3 سطح)

QUESTIONS = {
    "A1": [
        {"q": "Haus یعنی چی؟", "options": ["A) ماشین", "B) خانه", "C) کتاب", "D) میز"], "answer": "B", "type": "word"},
        {"q": "Buch یعنی چی؟", "options": ["A) آب", "B) کتاب", "C) در", "D) خانه"], "answer": "B", "type": "word"},
        {"q": "Hallo یعنی چی؟", "options": ["A) خداحافظ", "B) سلام", "C) ممنون", "D) بله"], "answer": "B", "type": "word"},
    ],

    "A2": [
        {"q": "Ich bin müde یعنی چی؟", "options": ["A) خسته‌ام", "B) خوشحالم", "C) می‌روم", "D) می‌خورم"], "answer": "A", "type": "sentence"},
        {"q": "Ich gehe zur Schule یعنی چی؟", "options": ["A) می‌خوابم", "B) به مدرسه می‌روم", "C) می‌نویسم", "D) می‌خورم"], "answer": "B", "type": "sentence"},
    ],

    "B1": [
        {"q": "من دیروز به مدرسه رفتم → آلمانی؟", "answer": "Ich bin gestern zur Schule gegangen", "type": "translate"},
        {"q": "Er ___ nach Hause (gehen)", "answer": "geht", "type": "grammar"},
    ]
}

# 🟢 منو
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 کلاس آنلاین رایگان", url="https://t.me/+Gq6nK-16B7Y2OTk0")],
        [InlineKeyboardButton("📊 تعیین سطح", callback_data="level")],
        [InlineKeyboardButton("🆘 پشتیبانی", url="https://t.me/ketabun")],
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت به منو", callback_data="home")],
        [InlineKeyboardButton("❌ لغو آزمون", callback_data="cancel")]
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
        "📌 ترجمه + تعیین سطح هوشمند\n"
        "💡 فقط یک کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 📊 شروع آزمون
async def start_level(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    user_state[user_id] = {
        "level": "A1",
        "score": 0,
        "asked": [],
        "step": 0
    }

    q = random.choice(QUESTIONS["A1"])
    user_state[user_id]["asked"].append(q)

    await query.message.reply_text(
        "📊 آزمون هوشمند شروع شد 🇩🇪\n\n" +
        q["q"] + "\n" + "\n".join(q.get("options", [])),
        reply_markup=back_menu()
    )

# ⚙️ دکمه‌ها
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "level":
        await start_level(update, context)
        return

    if query.data == "home":
        await query.edit_message_text("👋 منوی اصلی", reply_markup=main_menu())
        return

    if query.data == "cancel":
        user_state.pop(query.from_user.id, None)
        await query.edit_message_text("❌ آزمون لغو شد", reply_markup=main_menu())
        return

# 🧠 منطق هوشمند آزمون
def get_next_level(level):
    if level == "A1":
        return "A2"
    if level == "A2":
        return "B1"
    return "B1"

def pick_question(level, asked):
    pool = QUESTIONS[level]
    remaining = [q for q in pool if q not in asked]
    if not remaining:
        return None
    return random.choice(remaining)

# 🧠 پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.effective_user.id

    # 📊 اگر آزمون فعال است
    if user_id in user_state:

        state = user_state[user_id]
        level = state["level"]

        current_q = state.get("current")

        # بررسی جواب
        if current_q:

            correct = current_q["answer"]

            if text.strip().lower() == correct.lower():
                state["score"] += 1

            state["step"] += 1

            # ارتقا سطح
            if state["step"] >= 2:

                if state["score"] >= 1:
                    level = get_next_level(level)

                # نتیجه نهایی
                await update.message.reply_text(
                    f"📊 نتیجه شما:\n🎯 سطح: {level}",
                    reply_markup=main_menu()
                )
                user_state.pop(user_id, None)
                return

        # سوال بعدی
        q = pick_question(level, state["asked"])

        if not q:
            await update.message.reply_text("📊 آزمون تمام شد", reply_markup=main_menu())
            user_state.pop(user_id, None)
            return

        state["current"] = q
        state["asked"].append(q)

        await update.message.reply_text(
            q["q"] + "\n" + "\n".join(q.get("options", [])),
            reply_markup=back_menu()
        )
        return

    # 🤖 ترجمه AI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو معلم زبان آلمانی هستی:
- فارسی → آلمانی + تلفظ
- آلمانی → فارسی
- اسم → آرتیکل
- کوتاه جواب بده
"""
            },
            {"role": "user", "content": text}
        ]
    )

    await update.message.reply_text(
        response.choices[0].message.content,
        reply_markup=main_menu()
    )

# 🚀 اجرا
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
