import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from image_handler import handle_photo
from voice_handler import handle_voice
from search_logic import handle_search, handle_more
from logger_utils import log_user_info
from datetime import datetime, timedelta

# Load environment
load_dotenv()
TELEGRAM_BOT_TOKEN_PRIVATE = os.getenv("TELEGRAM_BOT_TOKEN_PRIVATE")
PRIVATE_BOT_PASSCODE = os.getenv("PRIVATE_BOT_PASSCODE")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Timezone and scheduler
APP_TIMEZONE = timezone('UTC')
scheduler = AsyncIOScheduler(timezone=APP_TIMEZONE)

# Authorized users
user_access_times = {}

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_info(update, "started bot", context)
    user_id = update.message.from_user.id
    if user_id not in user_access_times:
        await update.message.reply_text("🔐 Please enter the access code to use the bot.")
    else:
        await update.message.reply_text("👋 Welcome! Send a plate number, name (en/ar), phone, or photo of a license plate to search.")
    print("🆔 Chat ID:", update.message.chat.id)

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in user_access_times and datetime.now() - user_access_times[user_id] < timedelta(hours=24):
        await handle_search(update, context)
        return

    if text == PRIVATE_BOT_PASSCODE:
        user_access_times[user_id] = datetime.now()
        log_user_info(update, "authorized with access code", context)
        await update.message.reply_text("✅ Access granted! Now send a plate #, name (any language), phone #, photo, and voice note.")
    else:
        log_user_info(update, "failed access attempt", context)
        await update.message.reply_text("❌ Invalid code.")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Unauthorized.")
        return
    users = "\n".join([str(uid) for uid in user_access_times]) or "(None)"
    await update.message.reply_text(f"👥 Authorized Users:\n{users}")

# Async Main
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN_PRIVATE).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^more$"), handle_more))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, authorize))
    app.add_handler(MessageHandler(filters.PHOTO, lambda u, c: handle_photo(u, c, user_access_times.keys())))
    app.add_handler(MessageHandler(filters.VOICE, lambda u, c: handle_voice(u, c, user_access_times.keys())))
    app.add_handler(MessageHandler(filters.PHOTO, lambda u, c: handle_photo(u, c, user_access_times.keys())))

    # Start the scheduler to handle timed tasks
    scheduler.start()
    
    # Run the app
    await app.run_polling()

# Apply nest_asyncio to allow nested event loops
if __name__ == "__main__":
    nest_asyncio.apply()  # Allows nested event loops
    loop = asyncio.get_event_loop()  # Get the event loop
    loop.run_until_complete(main())  # Run the main function until completion
