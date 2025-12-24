import nest_asyncio
nest_asyncio.apply()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "7956260913:AAEF7kYU4KdqTNIe_Mb5Zx72ofcZwMc80mo")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "https://t.me/+34QaNkIogjk1YzVl")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@CyperXcopilot")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "7971284841").split(",")))

# === GLOBAL DATA ===
giveaway_data = None
redeem_codes = {}

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
    participated = 0
    if giveaway_data and user.id in giveaway_data.get("participants", []):
        participated = 1
    
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

# === Winners List ===
async def winners_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    await query.edit_message_text(
        "🏆 *RECENT WINNERS*\n\n"
        "✨ *Latest Giveaway Winners:*\n"
        "• Coming soon...\n\n"
        "🎯 *Join current giveaway to become a winner!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === Back to Main ===
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_welcome_menu(update, context)

# === REDEEM COMMAND ===
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check membership
    if not await check_membership(user.id, context):
        return await ask_to_join(update, context)
    
    if not context.args:
        await update.message.reply_text(
            "🔑 *Usage:*\n`/redeem <CODE>`\n\n"
            "*Example:* `/redeem PREMIUM123`",
            parse_mode="Markdown"
        )
        return
    
    code = context.args[0].upper()
    
    if code in redeem_codes:
        code_data = redeem_codes[code]
        if code_data.get("claimed", False):
            await update.message.reply_text("❌ This code has already been claimed.")
        else:
            # Mark as claimed
            redeem_codes[code]["claimed"] = True
            redeem_codes[code]["user_id"] = user.id
            redeem_codes[code]["username"] = f"@{user.username}" if user.username else user.full_name
            redeem_codes[code]["claimed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            reward = code_data["reward"]
            msg = (
                "╔══════════════════════════╗\n"
                "     🎉 *REDEEM SUCCESSFUL!*\n"
                "╚══════════════════════════╝\n\n"
                f"👤 *User:* {user.mention_markdown()}\n"
                f"🔑 *Code:* `{code}`\n"
                f"🎁 *Reward:* {reward}\n\n"
                "💫 *Enjoy your reward!*\n"
                "📢 *Stay tuned for more giveaways!*"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid code. Please check and try again.")

# === ADD CODE COMMAND (Admin) ===
async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚙️ *Usage:*\n`/addcode <CODE> <REWARD>`\n\n"
            "*Example:* `/addcode PREMIUM123 Premium Account`",
            parse_mode="Markdown"
        )
        return
    
    code = context.args[0].upper()
    reward = " ".join(context.args[1:])
    
    if code in redeem_codes:
        await update.message.reply_text(f"❌ Code `{code}` already exists!", parse_mode="Markdown")
        return
    
    redeem_codes[code] = {
        "reward": reward,
        "claimed": False,
        "user_id": None,
        "username": None,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "added_by": user.id
    }
    
    await update.message.reply_text(
        f"✅ *Code Added Successfully!*\n\n"
        f"🔑 *Code:* `{code}`\n"
        f"🎁 *Reward:* {reward}\n\n"
        f"📅 Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode="Markdown"
    )

# === REDEEM WINNERS COMMAND (Admin) ===
async def redeem_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not redeem_codes:
        await update.message.reply_text("📭 No redeem codes added yet!")
        return
    
    claimed_codes = [code for code, info in redeem_codes.items() if info.get("claimed")]
    unclaimed_codes = [code for code, info in redeem_codes.items() if not info.get("claimed")]
    
    msg = "📊 *REDEEM CODES STATUS*\n\n"
    
    if claimed_codes:
        msg += "✅ *CLAIMED CODES:*\n"
        for code in claimed_codes:
            info = redeem_codes[code]
            username = info.get('username', 'Unknown')
            claimed_at = info.get('claimed_at', 'N/A')
            msg += f"• `{code}` → {info['reward']} by {username} at {claimed_at}\n"
        msg += "\n"
    
    if unclaimed_codes:
        msg += "🔄 *UNCLAIMED CODES:*\n"
        for code in unclaimed_codes:
            info = redeem_codes[code]
            msg += f"• `{code}` → {info['reward']}\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# === HELP COMMAND ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *VIRUSX GIVEAWAY BOT HELP*\n\n"
        "✨ *User Commands:*\n"
        "• `/start` - Start the bot\n"
        "• `/giveaway` - Check active giveaway\n"
        "• `/redeem <code>` - Redeem a code\n"
        "• `/help` - Show this help\n\n"
        "👑 *Admin Commands:*\n"
        "• `/giveaway <time> <unit> <winners> <prize>` - Create giveaway\n"
        "• `/addcode <code> <reward>` - Add redeem code\n"
        "• `/redeem_winners` - Show claimed codes\n\n"
        "🎯 *Examples:*\n"
        "`/giveaway 5 minutes 1 Premium Account`\n"
        "`/redeem PREMIUM123`\n"
        "`/addcode TESTCODE Free Premium`\n\n"
        "📢 *Join our channel for updates!*"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# === GIVEAWAY COMMAND ===
async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check membership
    if not await check_membership(user.id, context):
        return await ask_to_join(update, context)
    
    # Admin giveaway creation
    if user.id in ADMIN_IDS and len(context.args) >= 4:
        try:
            number = int(context.args[0])
            unit = context.args[1].lower()
            winner_count = int(context.args[2])
        except ValueError:
            await update.message.reply_text(
                "❌ *Usage:* `/giveaway <number> <unit> <winner_count> <prize_text>`",
                parse_mode="Markdown"
            )
            return
        
        # Convert time to seconds
        if unit.startswith("min"):
            duration = number * 60
            time_display = f"{number} minute{'s' if number > 1 else ''}"
        elif unit.startswith("hour"):
            duration = number * 3600
            time_display = f"{number} hour{'s' if number > 1 else ''}"
        elif unit.startswith("sec"):
            duration = number
            time_display = f"{number} second{'s' if number > 1 else ''}"
        else:
            await update.message.reply_text("❌ Invalid time unit! Use seconds, minutes, or hours.")
            return
        
        prize_text = " ".join(context.args[3:])
        
        global giveaway_data
        giveaway_data = {
            "chat_id": update.effective_chat.id,
            "message_id": None,
            "prize": prize_text,
            "winner_count": winner_count,
            "duration": duration,
            "end_time": time.time() + duration,
            "participants": [],
            "admin_id": user.id
        }
        
        text = (
            "╔══════════════════════════════════╗\n"
            "        🎉 *GIVEAWAY STARTED!* 🎉\n"
            "╚══════════════════════════════════╝\n\n"
            f"🎁 *Prize:* {prize_text}\n"
            f"⏱ *Duration:* {time_display}\n"
            f"🏆 *Winners:* {winner_count}\n"
            f"👥 *Joined:* 0\n\n"
            "👇 *Click below to join!*"
        )
        
        keyboard = [[InlineKeyboardButton("🎯 Join Giveaway", callback_data="join_giveaway")]]
        
        message = await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        giveaway_data["message_id"] = message.message_id
        
        # Start countdown
        asyncio.create_task(giveaway_countdown(context, message.message_id))
        await update.message.reply_text("✅ Giveaway successfully created!")
        
        return
    
    # Display active giveaway
    if giveaway_data:
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
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(
            "❌ *No active giveaway at the moment.*\n"
            "📢 *Stay tuned for upcoming giveaways!*",
            parse_mode="Markdown"
        )

# === JOIN GIVEAWAY ===
async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global giveaway_data
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Check membership
    if not await check_membership(user.id, context):
        await query.answer("❌ You must join the channel first!", show_alert=True)
        return
    
    if not giveaway_data:
        await query.answer("❌ No active giveaway!", show_alert=True)
        return
    
    if time.time() > giveaway_data["end_time"]:
        await query.answer("❌ Giveaway has ended!", show_alert=True)
        return
    
    if user.id not in giveaway_data["participants"]:
        giveaway_data["participants"].append(user.id)
        await query.answer(
            f"✅ Joined successfully!\n"
            f"Total participants: {len(giveaway_data['participants'])}",
            show_alert=True
        )
    else:
        await query.answer("⚠️ You already joined!", show_alert=True)

# === GIVEAWAY COUNTDOWN ===
async def giveaway_countdown(context: ContextTypes.DEFAULT_TYPE, message_id: int):
    global giveaway_data
    if not giveaway_data:
        return
    
    chat_id = giveaway_data["chat_id"]
    
    try:
        while giveaway_data and time.time() < giveaway_data["end_time"]:
            remaining = max(0, int(giveaway_data["end_time"] - time.time()))
            mins, secs = divmod(remaining, 60)
            hours, mins = divmod(mins, 60)
            
            time_left = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"
            
            text = (
                "╔══════════════════════════════════╗\n"
                "        🎉 *GIVEAWAY STARTED!* 🎉\n"
                "╚══════════════════════════════════╝\n\n"
                f"🎁 *Prize:* {giveaway_data['prize']}\n"
                f"⏱ *Time Left:* {time_left}\n"
                f"🏆 *Winners:* {giveaway_data['winner_count']}\n"
                f"👥 *Joined:* {len(giveaway_data['participants'])}\n\n"
                "👇 *Click below to join!*"
            )
            
            keyboard = [[InlineKeyboardButton("🎯 Join Giveaway", callback_data="join_giveaway")]]
            
            try:
                await context.bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Error updating giveaway message: {e}")
            
            await asyncio.sleep(30)
    
    except asyncio.CancelledError:
        logger.info("Giveaway countdown cancelled")
        return
    except Exception as e:
        logger.error(f"Error in giveaway_countdown: {e}")
    
    await end_giveaway(context)

# === END GIVEAWAY ===
async def end_giveaway(context: ContextTypes.DEFAULT_TYPE):
    global giveaway_data
    if not giveaway_data:
        return
    
    chat_id = giveaway_data["chat_id"]
    
    if not giveaway_data.get("participants"):
        await context.bot.send_message(chat_id, "❌ No participants joined this giveaway.")
        giveaway_data = None
        return
    
    try:
        winners = random.sample(
            giveaway_data["participants"],
            min(giveaway_data["winner_count"], len(giveaway_data["participants"]))
        )
        
        winners_text = ""
        for uid in winners:
            try:
                user = await context.bot.get_chat(uid)
                username = f"@{user.username}" if user.username else f"[User](tg://user?id={uid})"
            except Exception as e:
                logger.error(f"Error getting user info: {e}")
                username = f"[User](tg://user?id={uid})"
            winners_text += f"🏆 {username}\n"
        
        text = (
            "╔══════════════════════════════════╗\n"
            "        🎊 *GIVEAWAY ENDED!* 🎊\n"
            "╚══════════════════════════════════╝\n\n"
            f"🎁 *Prize:* {giveaway_data['prize']}\n"
            f"👥 *Participants:* {len(giveaway_data['participants'])}\n"
            f"🏆 *Winners:* {len(winners)}\n\n"
            f"{winners_text}\n"
            "🔥 *Congratulations to all the winners!*"
        )
        
        await context.bot.send_message(chat_id, text, parse_mode="Markdown")
        
        # DM winners
        for uid in winners:
            try:
                await context.bot.send_message(
                    uid,
                    f"🎉 *Congratulations! You won the giveaway!*\n\n"
                    f"🏆 *Prize:* {giveaway_data['prize']}\n\n"
                    f"Please contact {OWNER_USERNAME} to claim your prize!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error DMing winner {uid}: {e}")
        
    except Exception as e:
        logger.error(f"Error ending giveaway: {e}")
        await context.bot.send_message(chat_id, "❌ Error ending giveaway.")
    
    giveaway_data = None

# === ERROR HANDLER ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if ADMIN_IDS:
            await context.bot.send_message(
                ADMIN_IDS[0],
                f"❌ Bot Error: {context.error}"
            )
    except:
        pass

# === MAIN ===
async def main():
    try:
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
        app.add_handler(CallbackQueryHandler(winners_list, pattern="^winners_list$"))
        app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))

        # Error Handler
        app.add_error_handler(error_handler)

        logger.info("🤖 Bot Starting...")
        await app.initialize()
        await app.start()
        logger.info("✅ Bot is running!")
        
        await app.updater.start_polling()
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if 'app' in locals():
            await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except RuntimeError as e:
        logger.error(f"RuntimeError: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
