import nest_asyncio
nest_asyncio.apply()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio
import random
import time
import telegram
from datetime import datetime
import os
import logging

# === LOGGING ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIG (Railway এ পরিবেশ ভেরিয়েবল ব্যবহার) ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "7956260913:AAEF7kYU4KdqTNIe_Mb5Zx72ofcZwMc80mo")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "https://t.me/+34QaNkIogjk1YzVl")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@CyperXcopilot")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "7971284841").split(",")))

# === GLOBAL DATA ===
giveaway_data = None
redeem_codes = {}  # { "CODE123": {"reward": "Prize", "claimed": False, ...} }

# === HELPER: Check Membership ===
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await check_membership(user.id, context):
        await send_welcome_menu(update, context)
    else:
        await ask_to_join(update, context)

# === Join Prompt ===
async def ask_to_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Join Channel", url=CHANNEL_USERNAME)],
        [InlineKeyboardButton("✅ I've Joined", callback_data="joined")]
    ]
    msg = (
        "🚀 *Welcome to VirusX Giveaway Bot!*\n\n"
        "📢 To use the bot, you must join our official channel.\n"
        "👉 Click the button below to join, then press *I've Joined*."
    )
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# === Joined Callback ===
async def joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_membership(query.from_user.id, context):
        await query.edit_message_text("✅ Verification successful!")
        await send_welcome_menu(update, context)
    else:
        await query.answer("❌ You haven't joined yet!", show_alert=True)

# === Premium Welcome Menu ===
async def send_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎁 Active Giveaway", callback_data="active_giveaway"),
         InlineKeyboardButton("🔑 Redeem Code", callback_data="redeem_menu")],
        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
         InlineKeyboardButton("🏆 Winners", callback_data="winners_list")],
        [InlineKeyboardButton("📢 Channel", url=CHANNEL_USERNAME),
         InlineKeyboardButton("👤 Owner", url=f"https://t.me/{OWNER_USERNAME[1:]}")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help_menu")]
    ]
    welcome_text = (
        "╔══════════════════════════════════╗\n"
        "        🎉 *VIRUSX GIVEAWAY BOT* 🎉\n"
        "╚══════════════════════════════════╝\n\n"
        "✨ *Welcome to the ultimate giveaway experience!*\n\n"
        "🚀 **Features:**\n"
        "• 🎁 Daily Giveaways\n"
        "• 🔑 Instant Code Redemption\n"
        "• 📊 Live Statistics\n"
        "• 🏆 Winner Announcements\n\n"
        "👉 *Use the buttons below to navigate:*"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.effective_chat.send_message(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# === Redeem Menu ===
async def redeem_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")],
        [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{OWNER_USERNAME[1:]}")]
    ]
    await query.edit_message_text(
        "🔑 *REDEEM YOUR CODE*\n\n"
        "To redeem, use the command:\n"
        "`/redeem <CODE>`\n\n"
        "*Example:* `/redeem PREMIUM123`\n\n"
        "💎 Unlock exclusive rewards instantly!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === My Stats ===
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    participated = len([p for g in [giveaway_data] if g and user.id in g.get("participants", [])])
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    await query.edit_message_text(
        f"📊 *YOUR STATS*\n\n"
        f"👤 *User:* {user.mention_markdown()}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"🎯 *Giveaways Joined:* {participated}\n"
        f"🔑 *Codes Redeemed:* Coming Soon\n\n"
        f"🏅 *Keep participating to climb the leaderboard!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === Help Menu ===
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    help_text = (
        "📘 *HOW TO USE THE BOT*\n\n"
        "🎁 **Giveaways:**\n"
        "• Join active giveaways via /giveaway\n"
        "• Winners are picked automatically\n\n"
        "🔑 **Redeem Codes:**\n"
        "• Use `/redeem <CODE>`\n"
        "• Codes are case-insensitive\n\n"
        "👑 **Admin Commands:**\n"
        "• `/giveaway <time> <unit> <winners> <prize>`\n"
        "• `/addcode <CODE> <REWARD>`\n"
        "• `/redeem_winners`\n\n"
        "📢 *Stay tuned in the channel for new codes & giveaways!*"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# === Giveaway Creation & Display ===
async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_membership(user.id, context):
        return await ask_to_join(update, context)

    if user.id in ADMIN_IDS and len(context.args) >= 4:
        # Admin giveaway creation logic (same as before, but with enhanced UI)
        # ... [same as your existing giveaway creation code] ...
        pass
    else:
        # Display active giveaway
        if giveaway_data:
            # Enhanced UI for active giveaway
            remaining = max(0, int(giveaway_data["end_time"] - time.time()))
            mins, secs = divmod(remaining, 60)
            hours, mins = divmod(mins, 60)
            time_left = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"
            
            text = (
                "╔══════════════════════════════╗\n"
                "         🎁 *ACTIVE GIVEAWAY* 🎁\n"
                "╚══════════════════════════════╝\n\n"
                f"🏆 *Prize:* {giveaway_data['prize']}\n"
                f"⏳ *Ends in:* {time_left}\n"
                f"👥 *Participants:* {len(giveaway_data['participants'])}\n"
                f"🎯 *Winners:* {giveaway_data['winner_count']}\n\n"
                "👇 Click below to join!"
            )
            keyboard = [
                [InlineKeyboardButton("🎯 Join Giveaway", callback_data="join_giveaway")],
                [InlineKeyboardButton("📊 View Participants", callback_data="view_participants")]
            ]
            if update.callback_query:
                await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("❌ *No active giveaway at the moment.*", parse_mode="Markdown")

# === Back to Main ===
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_welcome_menu(update, context)

# === Add other handlers (join_giveaway, end_giveaway, redeem, add_code, redeem_winners, etc.) ===
# ... [আপনার আগের যুক্ত লজিক এখানে রেখে দিন, শুধু UI টেক্সট আপডেট করুন] ...

# === Main ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("giveaway", giveaway))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("addcode", add_code))
    app.add_handler(CommandHandler("redeem_winners", redeem_winners))
    app.add_handler(CommandHandler("help", help_command))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(joined_callback, pattern="^joined$"))
    app.add_handler(CallbackQueryHandler(join_giveaway, pattern="^join_giveaway$"))
    app.add_handler(CallbackQueryHandler(giveaway, pattern="^active_giveaway$"))
    app.add_handler(CallbackQueryHandler(redeem_menu, pattern="^redeem_menu$"))
    app.add_handler(CallbackQueryHandler(my_stats, pattern="^my_stats$"))
    app.add_handler(CallbackQueryHandler(help_menu, pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))

    # Error Handler
    app.add_error_handler(error_handler)

    # Start Polling
    await app.initialize()
    await app.start()
    logger.info("🤖 Bot is running on Railway!")
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
