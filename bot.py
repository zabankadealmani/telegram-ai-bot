import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 ربات فعاله")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    # ❌ سوال قیمت
    if "قیمت" in text or "هزینه" in text or "چنده" in text:
        await update.message.reply_text(
            "📚 ما قیمت‌فروشی نداریم 😊\n"
            "برای اطلاعات دوره‌ها و کلاس‌ها پیام بدید."
        )
        return

    # 📚 معرفی کلاس / زبانساز
    if "کلاس" in text or "زبان" in text or "زبانساز" in text:
        await update.message.reply_text(
            "📚 زبانساز:\n"
            "آموزش زبان آلمانی از سطح A1 تا C1 🇩🇪\n"
            "تمرکز روی مکالمه و یادگیری واقعی 💪"
        )
        return

    # 🧑‍💼 ثبت‌نام
    if "ثبت" in text or "نام" in text or "ثبت‌نام" in text:
        await update.message.reply_text(
            "📝 برای ثبت‌نام لطفاً به ادمین پیام بدید:\n"
            "@ketabun"
        )
        return

    # 💬 جواب عمومی
    await update.message.reply_text(
        "سلام 😊\n"
        "برای اطلاعات درباره کلاس‌های زبانساز سوال بپرس 👍"
    )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
