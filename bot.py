import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

# 🔑 CONFIG
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ADMIN_ID = 744748269

# 📢 کانال اجباری
CHANNEL_LINK = "https://t.me/+JZRkw2YnlpRlMTM0"

# 🎥 کلاس آنلاین (اگر اشتباهه فقط اینو عوض کن)
ONLINE_CLASS_LINK = "https://t.me/+VMSXWp62w-Q0MGQ8"

client = OpenAI(api_key=OPENAI_API_KEY)

# 📦 DB ساده
users = set()
users_data = {}
user_target = {}

# 🧭 MAIN MENU
def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📩 پشتیبانی Ketabun", url="https://t.me/Ketabun"),
            InlineKeyboardButton("📚 کانال آموزش آلمانی", url="https://t.me/+IcNQUW7bM_xjZjdk")
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
            InlineKeyboardButton("🧪 امادگی آزمون سفارت", url="https://t.me/+VMSXWp62w-Q0MGQ8")
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
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("👥 کاربران", callback_data="users")],
        [InlineKeyboardButton("📢 پیام گروهی", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users.add(user.id)
    users_data[user.id] = {
        "name": user.full_name,
        "username": user.username
    }

    await update.message.reply_text(
        "🇩🇪 خوش آمدی\n✍️ کلمه یا جمله بفرست",
        reply_markup=main_menu()
    )

# 🤖 AI DICTIONARY
def ai_translate(text):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Return EXACT:

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
            "content": f"Make 1 German sentence + Persian meaning: {word}"
        }]
    )

    return res.choices[0].message.content

# 💬 MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    # 🔐 FORCE JOIN
    if user_id not in users:

        await update.message.reply_text(
            "❌ برای استفاده باید عضو کانال بشی",
            reply_markup=join_keyboard()
        )
        return

    # 👨‍💼 SEND TO USER (ADMIN CHAT MODE)
    if user_id in user_target:

        target = user_target[user_id]

        await context.bot.send_message(
            chat_id=target,
            text=f"📩 پیام از ادمین:\n\n{text}"
        )

        await update.message.reply_text("✅ ارسال شد")
        del user_target[user_id]
        return

    # 🤖 AI RESPONSE
    result = ai_translate(text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مثال", callback_data=f"example:{text}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

    await update.message.reply_text(result, reply_markup=keyboard)

    # 📩 LOG TO ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 پیام کاربر\n👤 {user_id}\n💬 {text}"
    )

# 🔁 CALLBACKS
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ✅ JOIN
    if data == "check_join":

        await query.message.reply_text("✅ فعال شد")

    # 📘 EXAMPLE
    elif data.startswith("example:"):

        word = data.split(":", 1)[1]
        ex = ai_example(word)

        await query.message.reply_text(ex)

    # 🔙 BACK
    elif data == "back":

        await query.message.reply_text("🏠 منو", reply_markup=main_menu())

    # 👨‍💼 ADMIN
    elif query.from_user.id == ADMIN_ID:

        if data == "stats":

            await query.message.reply_text(f"📊 کاربران: {len(users)}")

        elif data == "users":

            keyboard = []

            for uid, info in users_data.items():

                keyboard.append([
                    InlineKeyboardButton(
                        info.get("name"),
                        callback_data=f"msg:{uid}"
                    )
                ])

            await query.message.reply_text(
                "👥 انتخاب کاربر:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data.startswith("msg:"):

            uid = int(data.split(":")[1])
            user_target[query.from_user.id] = uid

            await query.message.reply_text("✍️ پیام رو بنویس")

        elif data == "broadcast":

            await query.message.reply_text("📢 /broadcast متن")

# 📢 BROADCAST
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
