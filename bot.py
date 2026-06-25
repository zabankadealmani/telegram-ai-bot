import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ADMIN_ID = 744748269

# 🔗 LINKS
CHANNEL_LINK = "https://t.me/+JZRkw2YnlpRlMTM0"
ONLINE_CLASS_LINK = "https://t.me/+Gq6nK-16B7Y2OTk0"

client = OpenAI(api_key=OPENAI_API_KEY)

# 📦 DATABASE
users = set()
user_allowed = set()
users_info = {}

# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی Ketabun", url="https://t.me/Ketabun"),
            InlineKeyboardButton("📚 آموزش آلمانی", url="https://t.me/+IcNQUW7bM_xjZjdk")
        ],
        [
            InlineKeyboardButton("🎥 کلاس آنلاین رایگان", url=ONLINE_CLASS_LINK),
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

# 🔐 JOIN BUTTON
def join_keyboard():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 ورود به کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")]
    ])

# 👨‍💼 ADMIN PANEL
def admin_panel():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("👥 کاربران", callback_data="users")],
        [InlineKeyboardButton("📢 پیام گروهی", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users.add(user.id)

    users_info[user.id] = {
        "name": user.full_name,
        "username": user.username
    }

    await update.message.reply_text(
        "🇩🇪 خوش آمدی به ربات آلمانی\n✍️ کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 🤖 AI (FIXED FORMAT)
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Return EXACT format:

German word
Article + word
Plural
Persian pronunciation (ONLY ONE LINE)
Example sentence

WORD: {text}
"""
        }]
    )

    return res.choices[0].message.content

def ai_example(word):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Give 1 German sentence + Persian meaning: {word}"
        }]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER (FULL FIX)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id
    text = update.message.text

    # 🚫 BLOCK ALL COMMANDS (IMPORTANT FIX)
    if text.startswith("/"):
        return

    # 🔐 GATE (NO REAL CHECK)
    if user_id not in user_allowed:

        await update.message.reply_text(
            "📢 ابتدا در کانال زیر عضو شو و سپس روی «عضو شدم» کلیک کن.",
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

    # 📩 ADMIN LOG (CLEAN)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=
        f"📩 پیام جدید\n\n"
        f"👤 نام: {user.full_name}\n"
        f"🔹 یوزرنیم: @{user.username if user.username else 'ندارد'}\n"
        f"🆔 آیدی: {user.id}\n\n"
        f"💬 پیام:\n{text}"
    )

# 🔁 CALLBACKS
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ JOIN BUTTON
    if data == "check_join":

        user_allowed.add(query.from_user.id)

        await query.message.reply_text("✅ فعال شد")

    # 📘 EXAMPLE
    elif data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(ex)

    # 🔙 BACK
    elif data == "back":

        await query.message.reply_text("🏠 منو اصلی", reply_markup=main_menu())

    # 👨‍💼 ADMIN PANEL
    elif query.from_user.id == ADMIN_ID:

        if data == "stats":

            await query.message.reply_text(f"📊 کاربران: {len(users)}")

        elif data == "users":

            text = ""

            for uid, info in users_info.items():

                username = info["username"] if info["username"] else "ندارد"

                text += (
                    f"👤 {info['name']}\n"
                    f"🔹 @{username}\n"
                    f"🆔 {uid}\n\n"
                )

            await query.message.reply_text(text[:4000])

        elif data == "broadcast":

            await query.message.reply_text("📢 /broadcast پیام")

# 📢 BROADCAST (FIXED & CLEAN)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("❌ پیام بنویس")
        return

    sent = 0

    for u in users:

        try:
            await context.bot.send_message(chat_id=u, text=f"📢 {msg}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ ارسال شد به {sent}")

# 🚀 RUN BOT
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("admin", lambda u, c: u.message.reply_text("👨‍💼 پنل", reply_markup=admin_panel())))

    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
