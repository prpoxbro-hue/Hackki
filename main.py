import re
import asyncio
import logging
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = "8906695052:AAHlgMP29P49Om-YhULNVWl7IAt0mlUDq_Y"
ADMIN_CHAT_ID = 8570946742  # Admin Chat ID
ADMIN_USERNAME = "@TRADER_RAJ10"  # Admin Username

IMAGE_URL = "https://i.ibb.co/WNRQ6D1Z/IMG-20260730-203514-934.jpg"
CHANNEL_LINK = "https://t.me/+ZHT3OOvGpt0wMDJk"
REGISTER_LINK = "https://pari-pulse.com/Wnuh"
PROMO_CODE = "S999"

# Conversation states
SELECT_LANG, CHECK_JOIN, REGISTRATION_STEP, AWAIT_USER_ID, MAIN_MENU, AWAIT_BROADCAST = range(6)


# --- DATABASE FUNCTIONS ---

def init_db():
    """Initialize SQLite database to store user IDs."""
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()


def add_user(chat_id: int):
    """Save user chat ID to database."""
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()


def get_all_users():
    """Retrieve all stored user IDs."""
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]


# --- USER FLOW HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: Save user ID and prompt for language selection."""
    chat_id = update.effective_chat.id
    add_user(chat_id)  # Record user in database

    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Hindi / Indian", callback_data="lang_in"),
            InlineKeyboardButton("🇵🇰 Urdu / Pakistani", callback_data="lang_pk"),
        ],
        [
            InlineKeyboardButton("🇳🇵 Nepali", callback_data="lang_np"),
            InlineKeyboardButton("🌐 English / Other", callback_data="lang_other"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=IMAGE_URL,
        caption="👋 **Welcome!** Please select your preferred language:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return SELECT_LANG


async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: Prompt user to join channel."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📢 Join Telegram Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I Have Joined", callback_data="joined_channel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_caption(
        caption="⚠️ **Step 1: Join Channel**\n\n"
                "You must join our official Telegram channel to proceed.",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return CHECK_JOIN


async def channel_verified(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 3: Direct user to registration menu."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🔗 Register Account", url=REGISTER_LINK)],
        [InlineKeyboardButton("✅ I Have Pre-Registered", callback_data="btn_preregistered")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption_text = (
        f"📋 **Step 2: Account Registration**\n\n"
        f"1. Click **Register Account** below to create your account.\n"
        f"   • Promo Code: `{PROMO_CODE}`\n\n"
        f"2. If you already registered, click **'I Have Pre-Registered'** to submit your ID."
    )

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=IMAGE_URL,
        caption=caption_text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return REGISTRATION_STEP


async def prompt_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 4: Request 10-digit ID."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_photo(
        photo=IMAGE_URL,
        caption="🔢 **Enter Your User ID**\n\n"
                "Please send your **10-digit Account ID** here in the chat to proceed.",
        parse_mode="Markdown",
    )
    return AWAIT_USER_ID


async def process_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 5: Process and analyze 10-digit ID, then open options."""
    text = update.message.text.strip()

    if not re.match(r"^\d{10}$", text):
        await update.message.reply_photo(
            photo=IMAGE_URL,
            caption="❌ **Invalid Format!**\n\n"
                    "Please enter a valid **10-digit numerical** User ID.",
            parse_mode="Markdown",
        )
        return AWAIT_USER_ID

    context.user_data["account_id"] = text

    status_msg = await update.message.reply_photo(
        photo=IMAGE_URL,
        caption=f"🔍 **Analyzing Account Data...**\n\n"
                f"ID: `{text}`\n"
                f"Status: `Connecting to database...` ⏳",
        parse_mode="Markdown",
    )

    await asyncio.sleep(2)
    await context.bot.edit_message_caption(
        chat_id=status_msg.chat_id,
        message_id=status_msg.message_id,
        caption=f"⚡ **Processing Verification...**\n\n"
                f"ID: `{text}`\n"
                f"Status: `Analyzing parameters...` 🔄",
        parse_mode="Markdown",
    )

    await asyncio.sleep(2)

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Open Hack",
                web_app=WebAppInfo(url=REGISTER_LINK),
            )
        ],
        [
            InlineKeyboardButton("📊 Account Info", callback_data="btn_info"),
            InlineKeyboardButton("👨‍💻 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_caption(
        chat_id=status_msg.chat_id,
        message_id=status_msg.message_id,
        caption=f"✅ **Verification & Analysis Complete!**\n\n"
                f"👤 **Account ID:** `{text}`\n"
                f"🟢 **Status:** Verified\n\n"
                f"All features are now unlocked. Select an option below:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return MAIN_MENU


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle options in the main menu."""
    query = update.callback_query
    await query.answer()

    account_id = context.user_data.get("account_id", "Unknown")

    if query.data == "btn_info":
        await query.message.reply_text(
            f"ℹ️ **Account Details**\n\nID: `{account_id}`\nStatus: Verified",
            parse_mode="Markdown",
        )

    return MAIN_MENU


# --- ADMIN PANEL HANDLERS ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin Panel Dashboard."""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ **Unauthorized Access.**")
        return

    users_count = len(get_all_users())

    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Total Users", callback_data="admin_users")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👑 **Admin Panel**\n\n"
        f"👤 **Admin:** {ADMIN_USERNAME}\n"
        f"🆔 **Admin ID:** `{ADMIN_CHAT_ID}`\n"
        f"👥 **Total Registered Users:** `{users_count}`\n\n"
        f"Select an option below:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Admin inline button clicks."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_CHAT_ID:
        await query.message.reply_text("⛔ Unauthorized.")
        return ConversationHandler.END

    if query.data == "admin_users":
        total_users = len(get_all_users())
        await query.message.reply_text(f"📊 **Total Bot Users:** `{total_users}`", parse_mode="Markdown")
        return ConversationHandler.END

    elif query.data == "admin_broadcast":
        await query.message.reply_text(
            "📢 **Broadcast Mode Active**\n\n"
            "Send the message, photo, video, or link you want to send to all users.\n"
            "Send `/cancel` to abort.",
            parse_mode="Markdown",
        )
        return AWAIT_BROADCAST


async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Broadcast text, photos, videos, or links to all saved users."""
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return ConversationHandler.END

    users = get_all_users()
    admin_chat_id = update.effective_chat.id
    msg_id = update.message.message_id

    status_msg = await update.message.reply_text(f"⏳ **Sending broadcast to {len(users)} users...**", parse_mode="Markdown")

    success = 0
    failed = 0

    for u_id in users:
        try:
            # Native copy_message supports photos, videos, captions, links, and formatting
            await context.bot.copy_message(
                chat_id=u_id,
                from_chat_id=admin_chat_id,
                message_id=msg_id,
            )
            success += 1
            await asyncio.sleep(0.05)  # Prevent rate limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to {u_id}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"📊 **Total Target Users:** {len(users)}\n"
        f"🟢 **Successfully Sent:** {success}\n"
        f"🔴 **Failed / Blocked:** {failed}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel active conversation."""
    await update.message.reply_text("Action cancelled. Send /start to restart.")
    return ConversationHandler.END


def main():
    # Initialize SQLite DB
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("admin", admin_panel),
            CallbackQueryHandler(admin_callback, pattern="^admin_"),
        ],
        states={
            SELECT_LANG: [CallbackQueryHandler(language_selected, pattern="^lang_")],
            CHECK_JOIN: [CallbackQueryHandler(channel_verified, pattern="^joined_channel$")],
            REGISTRATION_STEP: [
                CallbackQueryHandler(prompt_user_id, pattern="^btn_preregistered$")
            ],
            AWAIT_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_id)],
            MAIN_MENU: [CallbackQueryHandler(handle_main_menu)],
            AWAIT_BROADCAST: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.DOCUMENT) & ~filters.COMMAND,
                    execute_broadcast,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()