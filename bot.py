import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 کلیدها
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "به ربات آموزش زبانساز خوش اومدی 🇩🇪"
    )

# 🧠 پردازش پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # 🚫 سوالات غیر مرتبط
    if any(word in text for word in ["فیلم", "موزیک", "اخبار", "بازی"]):
        await update.message.reply_text(
            "فقط درباره زبان آلمانی سوال بپرس 🇩🇪"
        )
        return

    # 🚫 قیمت
    if "قیمت" in text or "هزینه" in text or "چنده" in text:
        await update.message.reply_text(
            "📚 برای اطلاعات کلاس‌ها به پشتیبانی پیام بده: @ketabun"
        )
        return

    # 🤖 AI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "تو دستیار آموزش زبان آلمانی آموزشگاه زبانساز هستی.\n"
                    "کاملاً آموزشی، کوتاه و کاربردی جواب بده (حداکثر 2 خط).\n\n"

                    "وظایف:\n"
                    "- فارسی → آلمانی + تلفظ\n"
                    "- اگر کلمه اسم بود آرتیکل بده (der/die/das)\n"
                    "- اگر کاربر گفت 'مثال' → یک جمله کوتاه آلمانی + ترجمه فارسی بده\n"
                    "- جمله آلمانی → ترجمه فارسی\n\n"

                    "اطلاعات آموزشگاه:\n"
                    "- A1 تا B1: Starten Wir\n"
                    "- B2 به بالا: Sicher\n"
                    "- کلاس‌ها: نیمه‌خصوصی Google Meet\n"
                    "- مدرسین: ایرانی و نیتیو حرفه‌ای\n"
                    "- پشتیبانی: @ketabun\n\n"

                    "قیمت نده، فقط هدایت به پشتیبانی بده.\n"
                    "اگر سوال کاملاً بی‌ربط بود فقط بگو: فقط درباره زبان آلمانی سوال بپرس."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )

    answer = response.choices[0].message.content

    await update.message.reply_text(answer)

# 🚀 اجرا
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
