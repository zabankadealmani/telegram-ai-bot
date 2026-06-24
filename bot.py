import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

ADMIN_ID = 744748269
USERS_FILE = "users.json"

# 👥 لود کاربران
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

users = load_users()

# 🟢 استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)
    save_users(users)

    keyboard = [
        [InlineKeyboardButton("📚 کلاس‌ها", callback_data="class")],
        [InlineKeyboardButton("📖 کتاب‌ها", callback_data="book")],
        [InlineKeyboardButton("💬 پشتیبانی", callback_data="support")]
    ]

    await update.message.reply_text(
        "سلام 👋 به ربات زبانساز خوش اومدی 🇩🇪",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📌 دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "class":
        await query.edit_message_text(
            "📚 کلاس‌های زبانساز:\n"
            "A1-B1: Starten Wir\n"
            "B2+: Sicher\n\n"
            "کلاس‌ها آنلاین در Google Meet هستند.\n"
            "برای ثبت‌نام: @ketabun"
        )

    elif query.data == "book":
        await query.edit_message_text(
            "📖 کتاب‌ها:\n"
            "- A1 تا B1: Starten Wir\n"
            "- B2 تا C1: Sicher"
        )

    elif query.data == "support":
        await query.edit_message_text(
            "💬 برای پشتیبانی پیام بده:\n@ketabun"
        )

# 👑 پنل ادمین
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="users")]
    ]

    await update.message.reply_text(
        "👑 پنل ادمین",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 🧠 دکمه‌های ادمین
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    if query.data == "users":
        text = "👥 کاربران:\n\n"
        for i, u in enumerate(users, 1):
            text += f"{i}. {u}\n"
        await query.edit_message_text(text)

    elif query.data == "broadcast":
        await query.edit_message_text(
            "برای ارسال پیام همگانی بنویس:\n\n"
            "/sendall متن پیام"
        )

# 📢 ارسال همگانی
async def sendall(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

# 🤖 AI پاسخ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    users.add(update.effective_user.id)
    save_users(users)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
تو دستیار زبان آلمانی هستی.
کوتاه جواب بده (حداکثر 3 خط).

فارسی → آلمانی + تلفظ
اسم → آرتیکل
آلمانی → ترجمه فارسی
اگر مثال خواست → جمله کوتاه

کتاب:
Starten Wir A1-B1
Sicher B2+

کلاس‌ها آنلاین Google Meet
پشتیبانی @ketabun
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
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("sendall", sendall))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
