import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI
from gtts import gTTS

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = 744748269

client = OpenAI(api_key=OPENAI_API_KEY)

USERS_FILE = "users.json"

# 📦 USERS
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

# 🧭 MENU (FULL 2x2 STYLE)
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی و ثبت‌نام کلاس", url=LINKS["support"]),
            InlineKeyboardButton("📚 آموزش آلمانی", url=LINKS["edu"])
        ],
        [
            InlineKeyboardButton("🎥 کلاس آنلاین", url=LINKS["live"]),
            InlineKeyboardButton("🎬 فیلم", url=LINKS["film"])
        ],
        [
            InlineKeyboardButton("🎧 پادکست", url=LINKS["podcast"]),
            InlineKeyboardButton("🎵 آهنگ", url=LINKS["music"])
        ],
        [
            InlineKeyboardButton("🎓 اوسبیلدونگ", url=LINKS["ausbildung"]),
            InlineKeyboardButton("🧪 آمادگی آزمون سفارت", url=LINKS["exam"])
        ]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    users[uid] = {"level": "A1"}
    save_users(users)

    await update.message.reply_text(
        "🇩🇪 خوش آمدی به ربات آلمانی هوشمند\n\n"
        "✍️ یه کلمه یا جمله فارسی/آلمانی بفرست",
        reply_markup=main_menu()
    )

# 🤖 TRANSLATION
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Translate Persian ↔ German.

If word:
- German word
- article
- plural
- pronunciation (FA + EN)

If sentence:
- full translation

NO extra explanation

TEXT: {text}
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
            "content": f"Make 1 simple German sentence + Persian meaning: {word}"
        }]
    )

    return res.choices[0].message.content

# 🎤 VOICE (GERMAN ONLY)
def make_voice(text, filename="voice.mp3"):

    tts = gTTS(text=text, lang="de")
    tts.save(filename)
    return filename

# 💬 HANDLE MESSAGE
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

    # 🎤 VOICE (safe try)
    try:
        voice = make_voice(text)
        await update.message.reply_voice(voice=open(voice, "rb"))
    except:
        pass

# 🔁 CALLBACK
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(f"📘 مثال:\n\n{ex}")

# 👨‍💼 ADMIN BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("❌ پیام بده")
        return

    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {msg}")
        except:
            pass

    await update.message.reply_text("✅ ارسال شد")

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
