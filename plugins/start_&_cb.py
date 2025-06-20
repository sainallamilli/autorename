import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, timedelta
from helper.database import DARKXSIDE78
from config import Config, Txt
import aiohttp
from urllib.parse import quote
import string
import logging
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@Client.on_message(filters.private & filters.command(["token", "mytokens", "bal"]))
async def check_tokens(client, message: Message):
    user_id = message.from_user.id
    user_data = await DARKXSIDE78.col.find_one({"_id": user_id})
    
    if not user_data:
        return await message.reply_text("You're not registered yet! Send /start to begin.")
    
    # Get premium status
    is_premium = user_data.get("is_premium", False)
    premium_expiry = user_data.get("premium_expiry")
    
    # Check if premium is expired
    if is_premium and premium_expiry and datetime.now() > premium_expiry:
        is_premium = False
        await DARKXSIDE78.col.update_one(
            {"_id": user_id},
            {"$set": {"is_premium": False, "premium_expiry": None}}
        )

    # Prepare message
    token_count = user_data.get("token", 69)
    msg = [
        "🔑 **Your Account Status** 🔑",
        "",
        f"🏷️ **Premium Status:** {'✅ Active' if is_premium else '❌ Inactive'}"
    ]
    
    if is_premium and premium_expiry:
        expiry_str = "Never" if premium_expiry.year == 9999 else premium_expiry.strftime('%d %b %Y %H:%M')
        msg.append(f"⏳ **Premium Expiry:** {expiry_str}")
    else:
        msg.extend([
            f"🪙 **Available Tokens:** {token_count}",
            "",
            "1 token = 1 file rename",
            ""
        ])
    
    # Create buttons
    buttons = []
    if not is_premium:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Generate More Tokens", callback_data="gen_tokens")],
            [InlineKeyboardButton("💎 Get Premium", callback_data="premium_info")]
        ])
    else:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_tokens")]
        ])
    
    await message.reply_text(
        "\n".join(msg),
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^(gen_tokens|premium_info|refresh_tokens|token_back)$"))
async def token_buttons_handler(client, query: CallbackQuery):
    data = query.data
    
    if data == "gen_tokens":
        await query.message.edit_text(
            "🔗 **You can generate tokens using /gentoken** 🔗",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/Bots_Nations_Support")],
                [InlineKeyboardButton("« Back", callback_data="token_back")]
            ]),
            disable_web_page_preview=True
        )
    
    elif data == "premium_info":
        await query.message.edit_text(
            Txt.PREMIUM_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/Bots_Nations_Support")],
                [InlineKeyboardButton("« Back", callback_data="token_back")]
            ]),
            disable_web_page_preview=True
        )
    
    elif data == "refresh_tokens":
        await query.answer("Status refreshed!")
        await check_tokens(client, query.message)
        
    elif data == "token_back":
        await check_tokens(client, query.message)

@Client.on_message(filters.command("gentoken") & filters.private)
async def generate_token(client: Client, message: Message):
    user_id = message.from_user.id
    
    token_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=Config.TOKEN_ID_LENGTH))
    deep_link = f"https://t.me/{Config.BOT_USERNAME}?start={token_id}"
    
    short_url = await shorten_url(deep_link)
    if not short_url:
        return await message.reply("❌ Failed to generate token link. Please try again later.")
    
    await DARKXSIDE78.create_token_link(user_id, token_id, 100)
    
    await message.reply(
        f"🔑 **Get 100 Tokens**\n\n"
        f"Click the link below and complete the verification:\n{short_url}\n\n"
        "⚠️ **Link valid for 24 hours | One-time use only**",
        disable_web_page_preview=True
    )

async def handle_token_redemption(client: Client, message: Message, token_id: str):
    user_id = message.from_user.id
    
    try:
        # Atomically find a token that is not claimed and update it to be claimed.
        # This prevents race conditions.
        token_data = await DARKXSIDE78.token_links.find_one_and_update(
            {
                "_id": token_id,
                "claimed": False,
                "expires_at": {"$gt": datetime.now(pytz.utc)} # Check for expiry
            },
            {
                "$set": {
                    "claimed": True,
                    "claimed_by": user_id,
                    "claimed_at": datetime.now(pytz.utc)
                }
            }
        )

        if not token_data:
            return await message.reply("❌ **Invalid, expired, or already used token link.**")

        # Optional: Prevent users from claiming their own generated links
        if token_data.get('user_id') == user_id:
            return await message.reply("❌ You cannot claim a token link that you generated yourself.")
        
        # Add tokens to the user who claimed it
        await DARKXSIDE78.col.update_one(
            {"_id": user_id},
            {"$inc": {"token": token_data['tokens']}}
        )
        
        await message.reply(f"✅ **Success! {token_data['tokens']} tokens have been added to your account!**")

    except Exception as e:
        logger.error(f"Error during token redemption for token {token_id}: {e}")
        await message.reply("❌ An error occurred while processing your request. Please try again later.")

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    # Handle token redemption if 'start' command has a payload
    if len(message.command) > 1:
        token_id = message.command[1]
        await handle_token_redemption(client, message, token_id)
        # After handling the token, we still want to show the start message.
        # So we don't return here.

    user = message.from_user
    await DARKXSIDE78.add_user(client, message)

    m = await message.reply_text("ᴏɴᴇᴇ-ᴄʜᴀɴ!, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ \nᴡᴀɪᴛ ᴀ ᴍᴏᴍᴇɴᴛ. . .")
    await asyncio.sleep(0.4)
    await m.edit_text("🎊")
    await asyncio.sleep(0.5)
    await m.edit_text("⚡")
    await asyncio.sleep(0.5)
    await m.edit_text("ꜱᴛᴀʀᴛɪɴɢ...")
    await asyncio.sleep(0.4)
    await m.delete()

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
        [
            InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Bots_Nation'),
            InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/Bots_Nation_Support')
        ],
        [
            InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')
        ]
    ])

    start_pic = Config.START_PIC
    if start_pic:
        await message.reply_photo(
            photo=start_pic,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention),
            reply_markup=buttons,
            disable_web_page_preview=True
        )

async def shorten_url(deep_link: str) -> str:
    if not (Config.SHORTENER_API and Config.SHORTENER_URL):
        return deep_link
    
    params = {'api': Config.SHORTENER_API, 'url': quote(deep_link)}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.SHORTENER_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data.get('shortenedUrl', deep_link)
    except Exception as e:
        logger.error(f"URL shortening failed: {e}")
    return deep_link

@Client.on_callback_query(filters.regex("help"))
async def help_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
        ]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("about"))
async def about_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")],
            [InlineKeyboardButton("🔙 Back to About", callback_data="about")]
        ]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("start"))
async def start_callback(client, query: CallbackQuery):
    user = query.from_user
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
        [
            InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Bots_Nation'),
            InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/Bots_Nation_Support')
        ],
        [
            InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')
        ]
    ])
    
    await query.message.edit_text(
        text=Txt.START_TXT.format(user.mention),
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("source"))
async def source_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text="**📦 Source Code**\n\n"
             "This bot is open source and available on GitHub.\n"
             "Feel free to contribute or report issues!\n\n"
             "**🔗 Repository:** [GitHub](https://github.com/Codeflix-Bots/AutoRenameBot)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("commands"))
async def commands_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.HELP_TXT, # Using HELP_TXT directly as it contains the commands list
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
        ]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("close"))
async def close_callback(client, query: CallbackQuery):
    await query.message.delete()
