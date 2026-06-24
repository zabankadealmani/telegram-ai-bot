import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 کلیدها
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# 👑 آیدی ادمین
ADMIN_ID = 744748269

# 👥 کاربران (فعلاً موقت در رم)
users = set()

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "به ربات هوشمند زبانساز خوش اومدی 🇩🇪"
    )

# 📢 ارسال پیام همگانی (فقط ادمین)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("مثال:\n/broadcast سلام بچه‌ها")
        return

    msg = " ".join(context.args)

    sent = 0

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ ارسال شد برای {sent} نفر")

# 🧠 هندل پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # 👥 ذخیره کاربر
    users.add(user_id)

    # 📩 ارسال پیام به ادمین
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیام جدید\n👤 {user_name}\n🆔 {user_id}\n\n{text}"
        )
    except:
        pass

    # 🚫 پیام‌های غیر مرتبط
    if any(word in text.lower() for word in [
        "فوتبال", "فیلم", "موزیک", "سیاست", "ارز", "بیت کوین"
    ]):
        await update.message.reply_text(
            "لطفاً فقط درباره زبان آلمانی سؤال بپرس 🇩🇪"
        )
        return

    # 🚫 قیمت
    if "قیمت" in text or "هزینه" in text or "چنده" in text:
        await update.message.reply_text(
            "📚 برای اطلاعات کلاس‌ها لطفاً پیام بده: @ketabun"
        )
        return

    # 🤖 AI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "تو دستیار آموزش زبان آلمانی هستی.\n"
                    "فقط درباره زبان آلمانی جواب بده.\n"
                    "جواب‌ها حداکثر 3 خط باشند.\n\n"

                    "اگر فارسی داد → آلمانی + تلفظ\n"
                    "اگر اسم بود → آرتیکل بده\n"
                    "اگر آلمانی داد → ترجمه فارسی\n"
                    "اگر گفت مثال → یک جمله کوتاه بده\n\n"

                    "کتاب‌ها:\n"
                    "- A1 تا B1: Starten Wir\n"
                    "- B2 به بالا: Sicher\n\n"

                    "کلاس‌ها آنلاین در Google Meet هستند.\n"
                    "مدرسین ایرانی و نیتیو هستند.\n\n"

                    "قیمت نده، فقط بگو پیام بده @ketabun\n"
                    "اگر بی‌ربط بود بگو فقط درباره زبان آلمانی سؤال بپرس."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )

    await update.message.reply_text(response.choices[0].message.content)

# 🚀 اجرا
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
