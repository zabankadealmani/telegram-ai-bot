import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269

# 👥 ذخیره کاربران
users = set()

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    await update.message.reply_text(
        "سلام 👋\n"
        "ربات زبانساز فعال است 🇩🇪"
    )

# 📊 لیست کاربران برای ادمین
async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 لیست کاربران:\n\n"

    for u in users:
        text += f"{u}\n"

    await update.message.reply_text(text)

# 📢 پیام همگانی
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    for u in users:
        try:
            await context.bot.send_message(u, msg)
        except:
            pass

    await update.message.reply_text("✅ ارسال شد به همه کاربران")

# 👤 ارسال پیام به یک نفر (بدون دردسر)
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "مثال:\n/send شماره ردیف پیام"
        )
        return

    index = int(context.args[0]) - 1
    msg = " ".join(context.args[1:])

    user_list = list(users)

    if index < 0 or index >= len(user_list):
        await update.message.reply_text("❌ کاربر پیدا نشد")
        return

    user_id = user_list[index]

    try:
        await context.bot.send_message(user_id, msg)
        await update.message.reply_text("✅ ارسال شد")
    except:
        await update.message.reply_text("❌ ارسال نشد")

# 🧠 AI پاسخ‌دهی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    users.add(update.effective_user.id)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو دستیار زبان آلمانی هستی.
کوتاه جواب بده (حداکثر 3 خط).

فارسی → آلمانی + تلفظ
آلمانی → ترجمه فارسی
اگر مثال خواست → جمله کوتاه بده

کتاب:
A1-B1 Starten Wir
B2+ Sicher

کلاس‌ها آنلاین Google Meet
پشتیبانی: @ketabun
"""
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
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
