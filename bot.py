import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

CHANNEL_USERNAME = "@YourChannel"

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

# 🎯 LINKS
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

# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی و ثبت‌نام کلاس", url=LINKS["support"]),
            InlineKeyboardButton("📚 آموزش زبان آلمانی", url=LINKS["edu"])
        ],
        [
            InlineKeyboardButton("🎥 کلاس آنلاین رایگان", url=LINKS["live"]),
            InlineKeyboardButton("🎬 فیلم آلمانی", url=LINKS["film"])
        ],
        [
            InlineKeyboardButton("🎧 پادکست آلمانی", url=LINKS["podcast"]),
            InlineKeyboardButton("🎵 آهنگ آلمانی", url=LINKS["music"])
        ],
        [
            InlineKeyboardButton("🎓 اوسبیلدونگ", url=LINKS["ausbildung"]),
            InlineKeyboardButton("🧪 آمادگی آزمون سفارت", url=LINKS["exam"])
        ]
    ])

# 🔐 CHECK JOIN CHANNEL
async def is_member(bot, user_id):

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    users[uid] = {"level": "A1"}
    save_users(users)

    await update.message.reply_text(
        "🇩🇪 خوش آمدی\n\n✍️ یک کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 💣 AI DICTIONARY (FIXED FORMAT)
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
You are a German dictionary bot.

Return ONLY this format:

German:
Article:
Plural:
Pronunciation (Persian):
Example:

NO extra text.

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
            "content": f"Give 1 simple German sentence + Persian meaning for: {word}"
        }]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # 🔐 FORCE JOIN CHANNEL
    if not await is_member(context.bot, user_id):

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
        ])

        await update.message.reply_text(
            "❌ برای استفاده باید عضو کانال بشی",
            reply_markup=keyboard
        )
        return

    text = update.message.text
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

# 🔁 CALLBACK
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # 📘 EXAMPLE
    if data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(f"📘 مثال:\n\n{ex}")

    # 🔐 CHECK JOIN
    elif data == "check_join":

        if await is_member(context.bot, query.from_user.id):
            await query.message.reply_text("✅ دسترسی فعال شد")
        else:
            await query.message.reply_text("❌ هنوز عضو نشدی")

    # 👨‍💼 ADMIN
    elif data == "stats" and query.from_user.id == ADMIN_ID:
        await query.message.reply_text(f"📊 کاربران: {len(users)}")

    elif data == "users" and query.from_user.id == ADMIN_ID:
        text = "\n".join(list(users.keys())[:20])
        await query.message.reply_text(text)

# 👨‍💼 ADMIN PANEL
def admin_panel():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("👥 کاربران", callback_data="users")]
    ])

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "👨‍💼 پنل ادمین",
        reply_markup=admin_panel()
    )

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
