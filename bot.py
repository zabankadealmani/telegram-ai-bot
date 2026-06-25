import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ADMIN_ID = 744748269
CHANNEL_LINK = "https://t.me/+JZRkw2YnlpRlMTM0"

client = OpenAI(api_key=OPENAI_API_KEY)

# 📦 SIMPLE DB
users = set()
user_allowed = set()

# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی Ketabun", url="https://t.me/Ketabun"),
            InlineKeyboardButton("📚 آموزش آلمانی", url="https://t.me/+IcNQUW7bM_xjZjdk")
        ],
        [
            InlineKeyboardButton("🎥 کلاس آنلاین", url="https://t.me/+VMSXWp62w-Q0MGQ8"),
            InlineKeyboardButton("🎬 فیلم آلمانی", url="https://t.me/+5Ll-_PHEmfEwOWQ8")
        ],
        [
            InlineKeyboardButton("🎧 پادکست", url="https://t.me/+a5HK5Ktg1kNiY2E0"),
            InlineKeyboardButton("🎵 آهنگ", url="https://t.me/+p0_P4lFcvIo0NWI0")
        ],
        [
            InlineKeyboardButton("🎓 اوسبیلدونگ", url="https://t.me/+TFAMe1OSiBhmZDhk"),
            InlineKeyboardButton("🧪 آزمون سفارت", url="https://t.me/+VMSXWp62w-Q0MGQ8")
        ]
    ])

# 🔐 JOIN KEYBOARD
def join_keyboard():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ])

# 👨‍💼 ADMIN PANEL
def admin_panel():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="stats")],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="users")],
        [InlineKeyboardButton("📢 ارسال پیام گروهی", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users.add(update.effective_user.id)

    await update.message.reply_text(
        "🇩🇪 خوش آمدی به ربات آلمانی هوشمند\n\n✍️ کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 🤖 AI DICTIONARY
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Return ONLY:

German:
Article:
Plural:
Pronunciation (Persian):
Example:

WORD: {text}
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
            "content": f"Give 1 German sentence + Persian meaning: {word}"
        }]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    # 🔐 FORCE JOIN (simple)
    if user_id not in user_allowed:

        await update.message.reply_text(
            "❌ برای استفاده باید عضو کانال بشی",
            reply_markup=join_keyboard()
        )
        return

    # 🤖 AI RESPONSE
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

    # 👨‍💼 SEND COPY TO ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 پیام کاربر\n\n👤 ID: {user_id}\n💬 Text: {text}"
    )

# 🔁 CALLBACK ROUTER
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ JOIN CONFIRM
    if data == "check_join":

        user_allowed.add(query.from_user.id)
        await query.message.reply_text("✅ دسترسی فعال شد")

    # 📘 EXAMPLE
    elif data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(f"📘 مثال:\n\n{ex}")

    # 🔙 BACK
    elif data == "back":

        await query.message.reply_text("🏠 منو اصلی:", reply_markup=main_menu())

    # 👨‍💼 ADMIN STATS
    elif data == "stats" and query.from_user.id == ADMIN_ID:

        await query.message.reply_text(f"📊 تعداد کاربران: {len(users)}")

    # 👥 USERS LIST
    elif data == "users" and query.from_user.id == ADMIN_ID:

        text = "\n".join(str(u) for u in list(users)[:30])
        await query.message.reply_text(text)

    # 📢 BROADCAST MENU
    elif data == "broadcast" and query.from_user.id == ADMIN_ID:

        await query.message.reply_text("📢 استفاده:\n/broadcast پیام")

# 📢 BROADCAST COMMAND
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("❌ پیام بنویس")
        return

    sent = 0

    for user_id in users:

        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 {msg}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ ارسال شد به {sent} نفر")

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("admin", lambda u, c: u.message.reply_text("👨‍💼 پنل ادمین", reply_markup=admin_panel())))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
