import os
import json
import random
import tempfile
from gtts import gTTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(data):
    json.dump(data, open(USERS_FILE, "w"))

users = load_users()
user_test = {}

# 🎓 LINKS
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

# 🧭 MENU
def main_menu():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 پشتیبانی", url=LINKS["support"])],
        [InlineKeyboardButton("📚 آموزش آلمانی", url=LINKS["edu"])],
        [InlineKeyboardButton("🎥 کلاس آنلاین", url=LINKS["live"])],
        [InlineKeyboardButton("🎬 فیلم", url=LINKS["film"])],
        [InlineKeyboardButton("🎧 پادکست", url=LINKS["podcast"])],
        [InlineKeyboardButton("🎵 آهنگ", url=LINKS["music"])],
        [InlineKeyboardButton("🎓 اوسبیلدونگ", url=LINKS["ausbildung"])],
        [InlineKeyboardButton("🧪 آزمون", url=LINKS["exam"])]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    users[uid] = {"level": "A1"}
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی 🇩🇪\n✍️ ترجمه + تلفظ + ویس",
        reply_markup=main_menu()
    )

# 🤖 TRANSLATION AI
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "German teacher"},
            {"role": "user", "content": f"""
Translate Persian ↔ German.

If word:
- translation
- article
- plural
- pronunciation (English + Persian)

If sentence:
- full translation
- pronunciation

NO examples
{text}
"""}
        ]
    )

    return res.choices[0].message.content

# 🎤 MAKE VOICE (FREE gTTS)
def make_voice(word):

    tts = gTTS(text=word, lang="de")

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(file.name)

    return file.name

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    text = update.message.text

    # 🧪 TEST MODE
    if uid in user_test:
        await check_answer(update, context)
        return

    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔊 تلفظ", callback_data=f"voice:{text}"),
            InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")
        ],
        [InlineKeyboardButton("🔙 برگشت", callback_data="home")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

# 📘 EXAMPLE AI
def ai_example(word):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Make 1 simple German sentence + Persian meaning"},
            {"role": "user", "content": word}
        ]
    )

    return res.choices[0].message.content

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

    # 🔊 VOICE
    elif data.startswith("voice:"):

        word = data.split(":", 1)[1]

        audio = make_voice(word)

        await query.message.reply_voice(
            voice=open(audio, "rb")
        )

    elif data == "home":
        await query.message.reply_text("🏠 منو:", reply_markup=main_menu())

# 🚀 RUN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
