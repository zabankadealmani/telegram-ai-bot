import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات هوشمند زبانساز هستم 🤖")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # فیلتر قیمت (اختیاری)
    if "قیمت" in text or "چنده" in text:
        await update.message.reply_text(
            "📚 ما قیمت نمی‌دیم 😊\nبرای اطلاعات به @ketabun پیام بدید"
        )
        return

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "تو یک دستیار آموزش زبان آلمانی هستی. دوستانه، کوتاه و مفید جواب بده."
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
