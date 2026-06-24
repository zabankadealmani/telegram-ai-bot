import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269

# 📁 فایل ذخیره کاربران
USERS_FILE = "users.json"

# 🧠 لود کاربران از فایل
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

# 💾 ذخیره کاربران
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

users = load_users()

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)
    save_users(users)

    await update.message.reply_text(
        "سلام 👋\n"
        "ربات زبانساز فعال است 🇩🇪"
    )

# 👥 لیست کاربران
async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 کاربران:\n\n"
    for i, u in enumerate(list(users), start=1):
        text += f"{i}. {u}\n"

    await update.message.reply_text(text)

# 📢 پیام همگانی
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    sent = 0

    for u in users:
        try:
            await context.bot.send_message(u, msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ ارسال شد به {sent} نفر")

# 👤 پیام به یک نفر با شماره لیست
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("مثال:\n/send 1 سلام")
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

# 🧠 AI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    user_id = update.effective_user.id
    users.add(user_id)
    save_users(users)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو دستیار زبان آلمانی آموزشگاه زبانساز هستی.
کوتاه جواب بده (حداکثر 3 خط).

فارسی → آلمانی + تلفظ
اسم → آرتیکل بده
آلمانی → ترجمه فارسی
اگر مثال خواست → جمله کوتاه

کتاب:
A1-B1 Starten Wir
B2+ Sicher

کلاس‌ها Google Meet
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
