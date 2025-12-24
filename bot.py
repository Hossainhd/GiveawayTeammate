import nest_asyncio
nest_asyncio.apply()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
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

# === HELPER FUNCTIONS ===
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False

async def ask_to_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Join Channel", url=CHANNEL_USERNAME)],
        [InlineKeyboardButton("✅ I've Joined", callback_data="joined")]
    ]
    msg = "🚀 *Welcome!*\n📢 Join our channel to continue."
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎁 Active Giveaway", callback_data="active_giveaway")],
        [InlineKeyboardButton("🔑 Redeem Code", callback_data="redeem_menu")],
        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
        [InlineKeyboardButton("📢 Channel", url=CHANNEL_USERNAME)]
    ]
    welcome_text = "✨ *Welcome to VirusX Giveaway Bot!* ✨"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.effective_chat.send_message(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await check_membership(user.id, context):
        await send_welcome_menu(update, context)
    else:
        await ask_to_join(update, context)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redeem a code"""
    user = update.effective_user
    
    if not await check_membership(user.id, context):
        return await ask_to_join(update, context)
    
    if not context.args:
        await update.message.reply_text("🔑 *Usage:* `/redeem <CODE>`", parse_mode="Markdown")
        return
    
    code = context.args[0].upper()
    
    if code in redeem_codes:
        code_data = redeem_codes[code]
        if code_data.get("claimed", False):
            await update.message.reply_text("❌ Already claimed.")
        else:
            redeem_codes[code]["claimed"] = True
            redeem_codes[code]["user_id"] = user.id
            redeem_codes[code]["username"] = f"@{user.username}" if user.username else user.full_name
            await update.message.reply_text(f"✅ Redeemed: {code_data['reward']}")
    else:
        await update.message.reply_text("❌ Invalid code.")

async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new redeem code (Admin only)"""
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("⚙️ Usage: `/addcode <CODE> <REWARD>`", parse_mode="Markdown")
        return
    
    code = context.args[0].upper()
    reward = " ".join(context.args[1:])
    
    if code in redeem_codes:
        await update.message.reply_text(f"❌ Code `{code}` exists!", parse_mode="Markdown")
        return
    
    redeem_codes[code] = {
        "reward": reward,
        "claimed": False,
        "user_id": None,
        "username": None,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    await update.message.reply_text(f"✅ Added: `{code}` → {reward}", parse_mode="Markdown")

async def redeem_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show redeem winners (Admin only)"""
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized.")
        return
    
    if not redeem_codes:
        await update.message.reply_text("📭 No codes yet!")
        return
    
    claimed = [code for code, info in redeem_codes.items() if info.get("claimed")]
    unclaimed = [code for code, info in redeem_codes.items() if not info.get("claimed")]
    
    msg = "📊 *Redeem Status:*\n\n"
    
    if claimed:
        msg += "✅ *Claimed:*\n"
        for code in claimed:
            info = redeem_codes[code]
            msg += f"• `{code}` → {info['reward']} by {info.get('username','Unknown')}\n"
        msg += "\n"
    
    if unclaimed:
        msg += "🔄 *Unclaimed:*\n"
        for code in unclaimed:
            info = redeem_codes[code]
            msg += f"• `{code}` → {info['reward']}\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = (
        "🤖 *VirusX Giveaway Bot*\n\n"
        "*Commands:*\n"
        "`/start` - Start bot\n"
        "`/giveaway` - Check giveaway\n"
        "`/redeem <code>` - Redeem code\n"
        "`/help` - This message\n\n"
        "*Admin:*\n"
        "`/giveaway <time> <unit> <winners> <prize>`\n"
        "`/addcode <code> <reward>`\n"
        "`/redeem_winners`"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle giveaway commands"""
    user = update.effective_user
    
    if not await check_membership(user.id, context):
        return await ask_to_join(update, context)
    
    # Admin create giveaway
    if user.id in ADMIN_IDS and len(context.args) >= 4:
        try:
            number = int(context.args[0])
            unit = context.args[1].lower()
            winner_count = int(context.args[2])
        except ValueError:
            await update.message.reply_text("❌ Usage: `/giveaway <number> <unit> <winners> <prize>`", parse_mode="Markdown")
            return
        
        # Time conversion
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
            await update.message.reply_text("❌ Invalid time unit!")
            return
        
        prize_text = " ".join(context.args[3:])
        
        global giveaway_data
        giveaway_data = {
            "chat_id": update.effective_chat.id,
            "prize": prize_text,
            "winner_count": winner_count,
            "end_time": time.time() + duration,
            "participants": []
        }
        
        text = f"🎉 *GIVEAWAY!*\n\n🎁 Prize: {prize_text}\n⏱ Duration: {time_display}\n🏆 Winners: {winner_count}\n👥 Joined: 0"
        keyboard = [[InlineKeyboardButton("🎯 Join", callback_data="join_giveaway")]]
        
        message = await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        giveaway_data["message_id"] = message.message_id
        asyncio.create_task(giveaway_countdown(context, message.message_id))
        await update.message.reply_text("✅ Giveaway created!")
        return
    
    # Show active giveaway
    if giveaway_data:
        remaining = max(0, int(giveaway_data["end_time"] - time.time()))
        mins, secs = divmod(remaining, 60)
        hours, mins = divmod(mins, 60)
        time_left = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"
        
        text = f"🎁 *ACTIVE GIVEAWAY*\n\n🏆 Prize: {giveaway_data['prize']}\n⏳ Ends in: {time_left}\n👥 Participants: {len(giveaway_data['participants'])}"
        keyboard = [[InlineKeyboardButton("🎯 Join", callback_data="join_giveaway")]]
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❌ No active giveaway.")

# === CALLBACK HANDLERS ===
async def joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_membership(query.from_user.id, context):
        await query.edit_message_text("✅ Verified!")
        await send_welcome_menu(update, context)
    else:
        await query.answer("❌ Not joined!", show_alert=True)

async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if not await check_membership(user.id, context):
        await query.answer("❌ Join channel first!", show_alert=True)
        return
    
    if not giveaway_data:
        await query.answer("❌ No giveaway!", show_alert=True)
        return
    
    if time.time() > giveaway_data["end_time"]:
        await query.answer("❌ Ended!", show_alert=True)
        return
    
    if user.id not in giveaway_data["participants"]:
        giveaway_data["participants"].append(user.id)
        await query.answer(f"✅ Joined! Total: {len(giveaway_data['participants'])}", show_alert=True)
    else:
        await query.answer("⚠️ Already joined!", show_alert=True)

async def redeem_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    await query.edit_message_text(
        "🔑 *REDEEM*\n\nUse: `/redeem <CODE>`\nExample: `/redeem PREMIUM123`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    participated = 1 if giveaway_data and user.id in giveaway_data.get("participants", []) else 0
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    await query.edit_message_text(
        f"📊 *STATS*\n👤 User: {user.mention_markdown()}\n🎯 Joined: {participated}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    await query.edit_message_text(
        "📘 *HELP*\nUse /help command for details.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_welcome_menu(update, context)

# === UTILITY FUNCTIONS ===
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
            
            text = f"🎉 *GIVEAWAY!*\n\n🎁 Prize: {giveaway_data['prize']}\n⏱ Time Left: {time_left}\n🏆 Winners: {giveaway_data['winner_count']}\n👥 Joined: {len(giveaway_data['participants'])}"
            keyboard = [[InlineKeyboardButton("🎯 Join", callback_data="join_giveaway")]]
            
            try:
                await context.bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Update error: {e}")
            
            await asyncio.sleep(30)
    
    except asyncio.CancelledError:
        return
    
    await end_giveaway(context)

async def end_giveaway(context: ContextTypes.DEFAULT_TYPE):
    global giveaway_data
    if not giveaway_data:
        return
    
    chat_id = giveaway_data["chat_id"]
    
    if not giveaway_data.get("participants"):
        await context.bot.send_message(chat_id, "❌ No participants.")
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
            except:
                username = f"[User](tg://user?id={uid})"
            winners_text += f"🏆 {username}\n"
        
        text = f"🎊 *GIVEAWAY ENDED!*\n\n🎁 Prize: {giveaway_data['prize']}\n👥 Participants: {len(giveaway_data['participants'])}\n🏆 Winners:\n{winners_text}"
        await context.bot.send_message(chat_id, text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"End error: {e}")
    
    giveaway_data = None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

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

        # Callback Handlers
        app.add_handler(CallbackQueryHandler(joined_callback, pattern="^joined$"))
        app.add_handler(CallbackQueryHandler(join_giveaway, pattern="^join_giveaway$"))
        app.add_handler(CallbackQueryHandler(giveaway, pattern="^active_giveaway$"))
        app.add_handler(CallbackQueryHandler(redeem_menu, pattern="^redeem_menu$"))
        app.add_handler(CallbackQueryHandler(my_stats, pattern="^my_stats$"))
        app.add_handler(CallbackQueryHandler(help_menu, pattern="^help_menu$"))
        app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))

        # Error Handler
        app.add_error_handler(error_handler)

        logger.info("🤖 Bot starting...")
        await app.initialize()
        await app.start()
        logger.info("✅ Bot running!")
        
        await app.updater.start_polling()
        
        # Keep alive
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Fatal: {e}")
    finally:
        if 'app' in locals():
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
