from config import Config, Txt
from helper.database import DARKXSIDE78
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import os, sys, time, asyncio, logging, datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ADMIN_USER_ID = Config.ADMIN

# Flag to indicate if the bot is restarting
is_restarting = False

async def get_user_by_ref(user_ref):
    &quot;&quot;&quot;Find a user by username or ID.&quot;&quot;&quot;
    if user_ref.startswith(&quot;@&quot;):
        return await DARKXSIDE78.col.find_one({&quot;username&quot;: user_ref[1:]})
    else:
        try:
            return await DARKXSIDE78.col.find_one({&quot;_id&quot;: int(user_ref)})
        except ValueError:
            return None

@Client.on_message(filters.private &amp; filters.command(&quot;restart&quot;) &amp; filters.user(ADMIN_USER_ID))
async def restart_bot(b, m):
    await m.reply_text(&quot;Restarting...&quot;)
    os.execl(sys.executable, sys.executable, &quot;-m&quot;, &quot;bot&quot;)

@Client.on_message(filters.private &amp; filters.command(&quot;leaderboard&quot;))
async def show_leaderboard(bot: Client, message: Message):
    try:
        users = await DARKXSIDE78.col.find().sort(&quot;rename_count&quot;, -1).limit(10).to_list(10)
        leaderboard = [&quot;&lt;b&gt;🏆 Top 10 Renamers 🏆&lt;/b&gt;\n&quot;]
        
        for idx, user in enumerate(users, 1):
            name = user.get(&#39;first_name&#39;, &#39;Unknown&#39;).strip() or &quot;Anonymous&quot;
            username = f&quot;@{user[&#39;username&#39;]}&quot; if user.get(&#39;username&#39;) else &quot;No UN&quot;
            count = user.get(&#39;rename_count&#39;, 0)
            leaderboard.append(
                f&quot;&lt;b&gt;{idx}.&lt;/b&gt; {name} &quot;
                f&quot;&lt;i&gt;({username})&lt;/i&gt; ➠ &quot;
                f&quot;&lt;code&gt;{count}&lt;/code&gt; ✨&quot;
            )
        
        await message.reply_text(&quot;\n&quot;.join(leaderboard))
    except Exception as e:
        await message.reply_text(f&quot;Error generating leaderboard: {e}&quot;)

@Client.on_message(filters.command(&quot;add_token&quot;) &amp; filters.user(Config.ADMIN))
async def add_tokens(bot: Client, message: Message):
    try:
        _, amount, *user_info = message.text.split()
        user_ref = &quot; &quot;.join(user_info).strip()
        
        user = await get_user_by_ref(user_ref)
        
        if not user:
            return await message.reply_text(&quot;User not found!&quot;)
        
        new_tokens = int(amount) + user.get(&#39;token&#39;, 69)
        await DARKXSIDE78.col.update_one(
            {&quot;_id&quot;: user[&#39;_id&#39;]},
            {&quot;$set&quot;: {&quot;token&quot;: new_tokens}}
        )
        await message.reply_text(f&quot;✅ Added {amount} tokens to user {user[&#39;_id&#39;]}. New balance: {new_tokens}&quot;)
    except Exception as e:
        await message.reply_text(f&quot;Error: {e}\nUsage: /add_token &lt;amount&gt; @username/userid&quot;)

@Client.on_message(filters.command(&quot;remove_token&quot;) &amp; filters.user(Config.ADMIN))
async def remove_tokens(bot: Client, message: Message):
    try:
        _, amount, *user_info = message.text.split()
        user_ref = &quot; &quot;.join(user_info).strip()
        
        user = await get_user_by_ref(user_ref)
        
        if not user:
            return await message.reply_text(&quot;User not found!&quot;)
        
        new_tokens = max(0, user.get(&#39;token&#39;, 69) - int(amount))
        await DARKXSIDE78.col.update_one(
            {&quot;_id&quot;: user[&#39;_id&#39;]},
            {&quot;$set&quot;: {&quot;token&quot;: new_tokens}}
        )
        await message.reply_text(f&quot;✅ Removed {amount} tokens from user {user[&#39;_id&#39;]}. New balance: {new_tokens}&quot;)
    except Exception as e:
        await message.reply_text(f&quot;Error: {e}\nUsage: /remove_token &lt;amount&gt; @username/userid&quot;)

@Client.on_message(filters.command(&quot;add_premium&quot;) &amp; filters.user(Config.ADMIN))
async def add_premium(bot: Client, message: Message):
    try:
        cmd, user_ref, duration = message.text.split(maxsplit=2)
        duration = duration.lower()
        
        user = await get_user_by_ref(user_ref)
        
        if not user:
            return await message.reply_text(&quot;User not found!&quot;)
        
        if duration == &quot;lifetime&quot;:
            expiry = datetime(9999, 12, 31)
        else:
            num, unit = duration[:-1], duration[-1]
            unit_map = {
                &#39;h&#39;: &#39;hours&#39;,
                &#39;d&#39;: &#39;days&#39;,
                &#39;m&#39;: &#39;months&#39;,
                &#39;y&#39;: &#39;years&#39;
            }
            delta = timedelta(**{unit_map[unit]: int(num)})
            expiry = datetime.now() + delta
        
        await DARKXSIDE78.col.update_one(
            {&quot;_id&quot;: user[&#39;_id&#39;]},
            {&quot;$set&quot;: {
                &quot;is_premium&quot;: True,
                &quot;premium_expiry&quot;: expiry
            }}
        )
        await message.reply_text(f&quot;✅ Premium added until {expiry}&quot;)
    except Exception as e:
        await message.reply_text(f&quot;Error: {e}\nUsage: /add_premium @username/userid 1d (1h/1m/1y/lifetime)&quot;)

@Client.on_message(filters.command(&quot;remove_premium&quot;) &amp; filters.user(Config.ADMIN))
async def remove_premium(bot: Client, message: Message):
    try:
        _, user_ref = message.text.split(maxsplit=1)
        
        user = await get_user_by_ref(user_ref)
        
        if not user:
            return await message.reply_text(&quot;User not found!&quot;)
        
        await DARKXSIDE78.col.update_one(
            {&quot;_id&quot;: user[&#39;_id&#39;]},
            {&quot;$set&quot;: {
                &quot;is_premium&quot;: False,
                &quot;premium_expiry&quot;: None
            }}
        )
        await message.reply_text(&quot;✅ Premium access removed&quot;)
    except Exception as e:
        await message.reply_text(f&quot;Error: {e}\nUsage: /remove_premium @username/userid&quot;)


@Client.on_message(filters.private &amp; filters.command(&quot;tutorial&quot;))
async def tutorial(bot: Client, message: Message):
    user_id = message.from_user.id
    format_template = await DARKXSIDE78.get_format_template(user_id)
    await message.reply_text(
        text=Txt.FILE_NAME_TXT.format(format_template=format_template),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(&quot;• ᴏᴡɴᴇʀ&quot;, url=&quot;https://t.me/darkxside78&quot;),
             InlineKeyboardButton(&quot;• ᴛᴜᴛᴏʀɪᴀʟ&quot;, url=&quot;https://t.me/+xp9acqFgosQ5NjNl&quot;)]
        ])
    )


@Client.on_message(filters.command([&quot;stats&quot;, &quot;status&quot;]) &amp; filters.user(Config.ADMIN))
async def get_stats(bot, message):
    total_users = await DARKXSIDE78.total_users_count()
    uptime = time.strftime(&quot;%Hh%Mm%Ss&quot;, time.gmtime(time.time() - bot.uptime))    
    start_t = time.time()
    st = await message.reply(&#39;**Accessing The Details.....**&#39;)    
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await st.edit(text=f&quot;**--Bot Status--** \n\n**⌚️ Bot Uptime :** {uptime} \n**🐌 Current Ping :** `{time_taken_s:.3f} ms` \n**👭 Total Users :** `{total_users}`&quot;)

@Client.on_message(filters.command(&quot;broadcast&quot;) &amp; filters.user(Config.ADMIN) &amp; filters.reply)
async def broadcast_handler(bot: Client, m: Message):
    await bot.send_message(Config.LOG_CHANNEL, f&quot;{m.from_user.mention} or {m.from_user.id} Is Started The Broadcast......&quot;)
    all_users = await DARKXSIDE78.get_all_users()
    broadcast_msg = m.reply_to_message
    sts_msg = await m.reply_text(&quot;Broadcast Started..!&quot;) 
    done = 0
    failed = 0
    success = 0
    start_time = time.time()
    total_users = await DARKXSIDE78.total_users_count()
    async for user in all_users:
        sts = await send_msg(user[&#39;_id&#39;], broadcast_msg)
        if sts == 200:
           success += 1
        else:
           failed += 1
        if sts == 400:
           await DARKXSIDE78.delete_user(user[&#39;_id&#39;])
        done += 1
        if not done % 20:
           await sts_msg.edit(f&quot;Broadcast In Progress: \n\nTotal Users {total_users} \nCompleted : {done} / {total_users}\nSuccess : {success}\nFailed : {failed}&quot;)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts_msg.edit(f&quot;Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ: \nCᴏᴍᴩʟᴇᴛᴇᴅ Iɴ `{completed_in}`.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}&quot;)
           
async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=int(user_id))
        return 200
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        logger.info(f&quot;{user_id} : Deactivated&quot;)
        return 400
    except UserIsBlocked:
        logger.info(f&quot;{user_id} : Blocked The Bot&quot;)
        return 400
    except PeerIdInvalid:
        logger.info(f&quot;{user_id} : User ID Invalid&quot;)
        return 400
    except Exception as e:
        logger.error(f&quot;{user_id} : {e}&quot;)
        return 500
