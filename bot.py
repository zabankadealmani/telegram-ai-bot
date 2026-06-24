import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 744748269

USERS_FILE = "users.json"

# 📦 DB
def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(data):
    json.dump(data, open(USERS_FILE, "w"))

users = load_users()

# 🧠 STATE
admin_state = {}

# 📚 MENU
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 تعیین سطح", callback_data="level")],
        [InlineKeyboardButton("🧠 ترجمه", callback_data="translate")],
    ])

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    users[uid] = {
        "name": update.effective_user.first_name
    }
    save_users(users)

    await update.message.reply_text(
        "👋 خوش آمدی!\n\n💡 یک کلمه یا جمله بفرست تا ترجمه کنم",
        reply_markup=main_menu()
    )

# 📩 پیام کاربران → ارسال به ادمین
async def forward_to_admin(update: Update):

    user = update.effective_user
    text = update.message.text

    msg = f"""
📩 پیام جدید

👤 نام: {user.first_name}
🆔 ID: {user.id}

💬 پیام:
{text}
"""

    await update.get_bot().send_message(
        chat_id=ADMIN_ID,
        text=msg
    )

# 🤖 پاسخ عادی ربات
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)
    text = update.message.text

    # ارسال به ادمین
    await forward_to_admin(update)

    # پاسخ ساده ترجمه
    await update.message.reply_text(
        f"🧠 ترجمه:\n{text}",
        reply_markup=main_menu()
    )

# 🛠 ADMIN PANEL
def admin_panel():
    buttons = []

    for uid, data in users.items():
        name = data.get("name", "User")

        buttons.append([
            InlineKeyboardButton(f"👤 {name}", callback_data=f"user_{uid}")
        ])

    buttons.append([
        InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast")
    ])

    return InlineKeyboardMarkup(buttons)

# 🛠 CALLBACKS
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    # 🔐 ADMIN PANEL
    if uid == ADMIN_ID:

        # لیست کاربران
        if query.data == "admin":
            await query.message.reply_text("🛠 پنل ادمین", reply_markup=admin_panel())
            return

        # انتخاب کاربر
        if query.data.startswith("user_"):

            target = query.data.replace("user_", "")

            admin_state["target"] = target
            admin_state["mode"] = "send_one"

            await query.message.reply_text("✍ پیام خود را ارسال کنید:")
            return

        # broadcast
        if query.data == "broadcast":

            admin_state["mode"] = "broadcast"
            await query.message.reply_text("📢 پیام همگانی را بنویسید:")
            return

    # 🧠 ترجمه / تعیین سطح
    if query.data == "translate":
        await query.message.reply_text("💬 فقط پیام بفرست تا ترجمه کنم")

# 💬 ADMIN MESSAGE HANDLER
async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    # 👑 اگر ادمین
    if uid == ADMIN_ID and "mode" in admin_state:

        # 📢 ارسال همگانی
        if admin_state["mode"] == "broadcast":

            for u in users:
                try:
                    await context.bot.send_message(chat_id=int(u), text=text)
                except:
                    pass

            await update.message.reply_text("✅ ارسال شد")
            admin_state.clear()
            return

        # 👤 ارسال تکی
        if admin_state["mode"] == "send_one":

            target = admin_state["target"]

            try:
                await context.bot.send_message(chat_id=int(target), text=text)
                await update.message.reply_text("✅ ارسال شد")
            except:
                await update.message.reply_text("❌ خطا")

            admin_state.clear()
            return

# 🚀 MAIN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(buttons))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message))

    app.run_polling()

if __name__ == "__main__":
    main()
