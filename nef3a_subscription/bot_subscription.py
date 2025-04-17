import os
import asyncio
import nest_asyncio
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pytz import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from subscription_db import (
    init_db, init_payment_table, is_user_active, activate_subscription,
    can_use_trial, increment_trial, get_trial_count,
    revoke_expired_subscriptions, reset_trial, record_payment
)

from binance_checker import check_usdt_payment
from image_handler import handle_photo
from voice_handler import handle_voice
from search_logic import handle_search

# Load env
load_dotenv()
TELEGRAM_BOT_TOKEN_MONETIZED = os.getenv("TELEGRAM_BOT_TOKEN_MONETIZED")
USDT_ADDRESS = os.getenv("USDT_ADDRESS") or "YOUR_WALLET_ADDRESS"
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
# Init
init_db()
init_payment_table()

pending_payments = {}
scheduler = AsyncIOScheduler(timezone=timezone('UTC'))
scheduler.start()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name

    buttons = [[InlineKeyboardButton("💸 Unlock with USDT", callback_data="pay_usdt")]]
    if can_use_trial(user_id):
        remaining = 3 - get_trial_count(user_id)
        buttons.append([InlineKeyboardButton(f"🎁 Free Trial ({remaining} left)", callback_data="free_trial")])

    reply_markup = InlineKeyboardMarkup(buttons)

    welcome_text = (
        "👋 *Welcome to Nef3a+!*\n\n"
        "🚗 This isn't your average car lookup bot.\n\n"
        "With *Nef3a+*, you can search Lebanese records using:\n"
        "🔎 License Plate Number\n"
        "📞 Phone Number\n"
        "👤 Name (Arabic or English)\n"
        "📸 Picture of a visible license plate — we detect it using AI\n"
        "🎤 Voice note — just say the person’s name, license plate, or phone\n\n"
        "🧪 You get *3 free trials* to test it out.\n"
        "💸 Or unlock full access instantly using USDT.\n\n"
        "👇 Choose an option below to begin:"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 el m3allim ma bysam7, enta mesh admin.")
        return

    conn = sqlite3.connect("subscription_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, trial_count, subscription_start, subscription_end, status FROM users")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("👤 ma fi wala user honi ya m3allim.")
        return

    msg = "📋 Users:\n\n"
    for row in rows:
        msg += (
            f"🆔 {row[0]}\n"
            f"🎁 Trial Used: {row[1]}/3\n"
            f"⏳ Start: {row[2]}\n"
            f"📅 End: {row[3]}\n"
            f"📌 Status: {row[4]}\n\n"
        )

    await update.message.reply_text(msg)
async def allpayments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 el m3allim ma bysam7, enta mesh admin.")
        return

    conn = sqlite3.connect("subscription_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, plan, amount, tx_id, timestamp FROM payments ORDER BY timestamp DESC LIMIT 30")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 No payments recorded yet.")
        return

    msg = "💳 *Last 30 Payments:*\n\n"
    for row in rows:
        msg += (
            f"👤 User ID: `{row[0]}`\n"
            f"📦 Plan: {row[1]}\n"
            f"💰 Amount: {row[2]} USDT\n"
            f"🆔 TxID: `{row[3]}`\n"
            f"🕒 Time: {row[4]}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")

# /plans
async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("🕐 1 Day — 20 USDT", callback_data="pay_1day")],
        [InlineKeyboardButton("📅 1 Week — 16 USDT", callback_data="pay_1week")],
        [InlineKeyboardButton("🗓️ 1 Month — 7 USDT", callback_data="pay_1month")],
        [InlineKeyboardButton("🧧 2 Months — 13 USDT", callback_data="pay_2months")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    text = (
        "💸 *Choose Your Plan:*\n\n"
        "• 🕐 *1 Day* — 20 USDT\n"
        "• 📅 *1 Week* — 16 USDT\n"
        "• 🗓️ *1 Month* — 7 USDT\n"
        "• 🧧 *2 Months* — 13 USDT\n\n"
        f"Send payment to:\n`{USDT_ADDRESS}`\n\n"
        "⏳ el m3allim will confirm and activate your subscription automatically."
    )

    # Fix: handle both /plans and button call
    message = update.message or update.callback_query.message
    await message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# Button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "free_trial":
        if can_use_trial(user_id):
            increment_trial(user_id)
            remaining = 3 - get_trial_count(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎁 Free trial activated! {remaining} trial(s) left. You now have access for 24h.\nSta3milna mni7 ya jefe."
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="🚫 Sorry jefe, no free trials left. Please unlock with USDT."
            )

    elif query.data == "pay_usdt":
        await plans(update, context)  # Reuse the same UI

    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        pending_payments[user_id] = {"plan": plan, "time": datetime.utcnow()}
        await context.bot.send_message(
            chat_id=user_id,
            text=f"💸 You selected *{plan}* plan.\n\nSend USDT to:\n`{USDT_ADDRESS}`\n\n✅ el m3allim will confirm & activate automatically.",
            parse_mode="Markdown"
        )

# Access control
async def authorized_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_active(user_id):
        await update.message.reply_text("🔍 el m3allim 3am yfattesh bel database...")
        await handle_search(update, context)
        return

    if can_use_trial(user_id):
        increment_trial(user_id)
        await update.message.reply_text("🎁 Trial used. el m3allim 3am yfattesh...")
        await handle_search(update, context)
    else:
        await update.message.reply_text("🚫 el m3allim: No trials left. Ba3et USDT to continue.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_active(user_id):
        await handle_photo(update, context, authorized_users={user_id})
    else:
        await update.message.reply_text("🖼️ el m3allim: Ba3et el masari aw ma teb3at soura.")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_active(user_id):
        await handle_voice(update, context, authorized_users={user_id})
    else:
        await update.message.reply_text("🎧 el m3allim ma bysam3ak lamma tkoun broke.")

# Check payments
async def auto_check_payments(app):
    for user_id, data in list(pending_payments.items()):
        plan = data["plan"]
        time_selected = data["time"]

        if datetime.utcnow() - time_selected > timedelta(minutes=30):
            del pending_payments[user_id]
            continue

        price_map = {"1day": 20, "1week": 16, "1month": 7, "2months": 13}
        duration_map = {"1day": 1, "1week": 7, "1month": 30, "2months": 60}

        payment = check_usdt_payment(min_amount=price_map[plan])
        if payment:
            activate_subscription(user_id, days=duration_map[plan])
            record_payment(
                user_id=user_id,
                plan=plan,
                amount=payment['amount'],
                tx_id=payment['tx_id'],
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            )
            await app.bot.send_message(
                user_id,
                f"✅ el m3allim: Payment of {payment['amount']} USDT received!\nTxID: `{payment['tx_id']}`\nYour *{plan}* plan is now active! Enjoy 🚀",
                parse_mode="Markdown"
            )
            del pending_payments[user_id]

# Reset trials
async def resetme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 el m3allim ma bysam7, enta mesh admin.")
        return

    reset_trial(update.effective_user.id)
    await update.message.reply_text("✅ Trial count reset for your user. Try clicking Free Trial again.")

# Run bot
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN_MONETIZED).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plans", plans))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("resetme", resetme))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, authorized_text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(CommandHandler("allpayments", allpayments))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, lambda update, context: update.message.reply_text("🚫 el m3allim ma bysam7, enta mesh admin.")))
    
    scheduler.add_job(auto_check_payments, "interval", seconds=20, args=[app])
    scheduler.add_job(lambda: revoke_expired_subscriptions(), "interval", minutes=10)
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
