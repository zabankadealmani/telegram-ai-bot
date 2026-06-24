import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269
USERS_FILE = "users.json"

# 👥 USERS
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(data):
    json.dump(data, open(USERS_FILE, "w"))

users = load_users()

# 🧠 STATES
user_state = {}
admin_state = {}

# 📚 MAIN MENU (UPDATED UI)
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 پشتیبانی و ثبت‌نام کلاس‌های آنلاین عادی و فشرده", url="https://t.me/ketabun")],

        [InlineKeyboardButton("🎓 کلاس آنلاین رایگان", url="https://t.me/+Gq6nK-16B7Y2OTk0")],

        [InlineKeyboardButton("📚 آموزش زبان آلمانی", url="https://t.me/almanibeasani1")],
        [InlineKeyboardButton("🎬 فیلم آلمانی با ترجمه", url="https://t.me/DeutscheAnimation_filmalmani")],
        [InlineKeyboardButton("🎧 پادکست آلمانی", url="https://t.me/germanpodcast_deutschepodcast")],
        [InlineKeyboardButton("💼 اوسبیلدونگ", url="https://t.me/ausbildung_parastar")],
        [InlineKeyboardButton("🎵 موزیک آلمانی", url="https://t.me/deutschemusik_musikalmani_tarjom")],

        [InlineKeyboardButton("🧪 آمادگی آزمون سفارت", url="https://t.me/goethepruefung")],

        [InlineKeyboardButton("📊 تعیین سطح هوشمند", callback_data="level")],
        [InlineKeyboardButton("🧠 ترجمه هوشمند", callback_data="translate")],

        [InlineKeyboardButton("🛠 پنل ادمین", callback_data="admin_panel")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users[str(user.id)] = {
        "username": user.username,
        "first_name": user.first_name,
        "joined": str(datetime.now())
    }
    save_users(users)

    await update.message.reply_text(
        "👋 به ربات آموزش زبان آلمانی خوش آمدی 🇩🇪\n\n"
        "📌 امکانات:\n"
        "✔ ترجمه فارسی ↔ آلمانی\n"
        "✔ تعیین سطح A1 تا B2\n"
        "✔ منابع آموزشی کامل\n\n"
        "💡 فقط یک کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 📊 ADMIN PANEL
def admin_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("👤 ارسال تکی", callback_data="send_one")],
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="stats")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
    ])

# 📊 QUESTIONS (A1 → B2)
QUESTIONS = {
    "A1": [
        {"q": "Haus یعنی چی؟", "a": "B"},
        {"q": "Buch یعنی چی؟", "a": "B"},
    ],
    "A2": [
        {"q": "Ich bin müde یعنی چی؟", "a": "A"},
        {"q": "Er geht zur Schule یعنی چی؟", "a": "B"},
    ],
    "B1": [
        {"q": "Ich ___ gestern gegangen (gehen)", "a": "ging"},
    ],
    "B2": [
        {"q": "ترجمه: من دیروز می‌رفتم", "a": "Ich bin gestern gegangen"},
    ]
}

# ⚙️ CALLBACKS
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    # HOME
    if query.data == "home":
        await query.message.edit_text("🏠 منوی اصلی", reply_markup=main_menu())
        return

    # LEVEL START
    if query.data == "level":

        user_state[uid] = {
            "level": "A1",
            "score": 0,
            "step": 0
        }

        q = QUESTIONS["A1"][0]

        user_state[uid]["current"] = q

        await query.message.reply_text(
            "📊 آزمون شروع شد 🇩🇪\n\n" + q["q"],
            reply_markup=back_menu()
        )
        return

    # ADMIN
    if query.data == "admin_panel":

        if uid != ADMIN_ID:
            await query.message.reply_text("⛔ دسترسی نداری")
            return

        await query.message.reply_text("🛠 پنل ادمین", reply_markup=admin_panel())
        return

    # STATS
    if query.data == "stats":
        await query.message.reply_text(f"👥 کاربران: {len(users)}")
        return

    # BROADCAST
    if query.data == "broadcast":
        admin_state["mode"] = "broadcast"
        await query.message.reply_text("✍ پیام همگانی:")
        return

    # SEND ONE
    if query.data == "send_one":
        admin_state["mode"] = "send_one"
        await query.message.reply_text("✍ ارسال تکی (id پیام)")
        return

# 🧠 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    uid = update.effective_user.id

    # 👑 ADMIN
    if uid == ADMIN_ID and "mode" in admin_state:

        mode = admin_state["mode"]

        if mode == "broadcast":
            for u in users:
                try:
                    await context.bot.send_message(chat_id=u, text=text)
                except:
                    pass
            await update.message.reply_text("✅ ارسال شد")
            admin_state.clear()
            return

        if mode == "send_one":
            try:
                target, msg = text.split(" ", 1)
                await context.bot.send_message(chat_id=int(target), text=msg)
                await update.message.reply_text("✅ ارسال شد")
            except:
                await update.message.reply_text("❌ فرمت اشتباه")
            admin_state.clear()
            return

    # 📊 LEVEL TEST
    if uid in user_state:

        state = user_state[uid]
        q = state["current"]

        if text.lower() == q["a"].lower():
            state["score"] += 1

        state["step"] += 1

        # result
        if state["step"] >= 2:

            score = state["score"]

            if score >= 2:
                level = "B2 🔴"
            elif score == 1:
                level = "B1 🔵"
            else:
                level = "A2 🟡"

            user_state.pop(uid, None)

            await update.message.reply_text(
                f"📊 نتیجه:\n🎯 سطح شما: {level}",
                reply_markup=main_menu()
            )
            return

        # next question
        next_q = random.choice(QUESTIONS["A1"])
        state["current"] = next_q

        await update.message.reply_text(next_q["q"])
        return

    # 🤖 TRANSLATION
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "تو معلم زبان آلمانی هستی. کوتاه و دقیق ترجمه کن."
            },
            {"role": "user", "content": text}
        ]
    )

    await update.message.reply_text(
        response.choices[0].message.content,
        reply_markup=main_menu()
    )

# 🚀 RUN
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
