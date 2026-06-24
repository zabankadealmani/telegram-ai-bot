import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 گرفتن کلیدها از Render Environment
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🤖 اتصال به OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "به ربات آموزش زبانساز خوش اومدی 🤖"
    )

# 🧠 هندل پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # 🚫 فیلتر سوالات غیر مرتبط (اختیاری)
    allowed_keywords = ["آلمانی", "deutsch", "زبان", "کتاب", "کلاس"]
    if not any(k in text.lower() for k in allowed_keywords) and len(text) < 3:
        await update.message.reply_text(
            "لطفاً فقط درباره زبان آلمانی سوال بپرس 🇩🇪"
        )
        return

    # 🚫 فیلتر قیمت
    if "قیمت" in text or "هزینه" in text or "چنده" in text:
        await update.message.reply_text(
            "📚 برای اطلاعات کلاس‌ها لطفاً به پشتیبان پیام بده: @ketabun"
        )
        return

    # 🤖 درخواست به ChatGPT
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "تو دستیار رسمی آموزشگاه زبانساز هستی.\n"
                    "فقط درباره زبان آلمانی جواب بده.\n"
                    "جواب‌ها حداکثر 2 خط باشند.\n"
                    "اگر سوال غیر مرتبط بود فقط بگو: لطفاً فقط درباره زبان آلمانی سوال بپرس.\n\n"

                    "قوانین ترجمه:\n"
                    "- فارسی → آلمانی + تلفظ\n"
                    "- اگر اسم بود آرتیکل بده (der/die/das)\n"
                    "- جمله آلمانی → ترجمه فارسی\n\n"

                    "کتاب‌ها:\n"
                    "- A1 تا B1: Starten Wir\n"
                    "- B2 به بالا: Sicher\n\n"

                    "کلاس‌ها:\n"
                    "- نیمه‌خصوصی\n"
                    "- آنلاین Google Meet\n"
                    "- مدرسین ایرانی و نیتیو\n\n"

                    "پشتیبانی: @ketabun\n"
                    "گاهی به شکل طبیعی پیشنهاد ثبت‌نام بده"
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
