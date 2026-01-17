import os, requests, re, cv2, asyncio, zipfile, shutil, random
from PIL import Image
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

LOG_CHANNEL_ID = -1003506657299 
SUDO_USERS = [7487670897, 8409591285] 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
BIO_WARNS = {} 

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_EXTREME_SONIC_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UI DESIGNS ---

DM_START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ɢᴜᴀʀᴅɪᴀɴ**
Status: `Extreme Sonic UI Mode Active` 🚀
━━━━━━━━━━━━━━━━━━━━
"""

BAN_CARD = """
✨ **ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ ɪɴsᴛᴀɴᴛʟʏ**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
📝 **Reason:** `{reason}`
🛠️ **Action:** `Full Extreme Cleanup + Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE TURBO FUNCTIONS ---

async def a1_turbo_cleanup(client, chat_id, user_id):
    """Background parallel history wipe"""
    msg_ids = []
    try:
        async for msg in client.get_chat_history(chat_id, limit=500):
            if msg.from_user and msg.from_user.id == user_id:
                msg_ids.append(msg.id)
                if len(msg_ids) >= 100:
                    await client.delete_messages(chat_id, msg_ids)
                    msg_ids = []
        if msg_ids: await client.delete_messages(chat_id, msg_ids)
    except errors.BotMethodInvalid:
        print("❌ Cleanup Failed: Upgrade group to Supergroup!")
    except Exception as e: print(f"❌ Cleanup Error: {e}")

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    if file_path.endswith((".webp", ".png", ".gif")):
        try:
            img = Image.open(file_path).convert("RGB")
            t_path = file_path + ".jpg"; img.save(t_path, "JPEG")
            file_path = t_path
        except: pass
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': open(file_path, 'rb')}, data=params)
        res = r.json()
        if res.get('status') == 'success':
            n = res['nudity']
            # Highly Sensitive Threshold
            if n['sexual_display'] > 0.10 or n['erotica'] > 0.10: return True
    except: pass
    return False

# --- HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start_dm(client, message):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")]])
    await message.reply_text(DM_START_TEXT, reply_markup=buttons)

@app.on_message(filters.command("scan") & filters.group)
async def extreme_scan(client, message):
    progress = await message.reply("🔎 **Extreme Scan in progress...**")
    count = 0
    try:
        async for msg in client.get_chat_history(message.chat.id, limit=500):
            if msg.photo or msg.sticker or msg.animation:
                try:
                    path = await msg.download(file_name=f"{DOWNLOAD_DIR}scan_{msg.id}")
                    if check_nsfw(path):
                        await msg.delete(); count += 1
                    if os.path.exists(path): os.remove(path)
                except: pass
        await progress.edit(f"✅ **Extreme Scan Complete!** {count} items removed.")
    except errors.BotMethodInvalid:
        await progress.edit("❌ **Error:** Scan feature only works in **Supergroups**. Please upgrade this group!")

@app.on_message(filters.group & filters.new_chat_members)
async def extreme_join_guard(client, message: Message):
    for u in message.new_chat_members:
        try:
            # 1. Profile Photo Scan
            photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
            if photos:
                path = await client.download_media(photos[0].file_id, file_name=f"{DOWNLOAD_DIR}pfp_{u.id}.jpg")
                if check_nsfw(path):
                    await message.chat.ban_member(u.id)
                    await message.reply_text(BAN_CARD.format(user=u.mention, user_id=u.id, reason="NSFW Profile Picture"))
                    if os.path.exists(path): os.remove(path)
                    continue 
                if os.path.exists(path): os.remove(path)

            # 2. Bio Link & NSFW Detect
            full_user = await client.get_chat(u.id)
            bio, name = (full_user.bio or "").lower(), f"{u.first_name} {u.username or ''}".lower()
            
            if "http" in bio or "t.me/" in bio:
                BIO_WARNS[u.id] = BIO_WARNS.get(u.id, 0) + 1
                if BIO_WARNS[u.id] >= 3:
                    await message.chat.restrict_member(u.id, ChatPermissions(can_send_messages=False))
                    await message.reply(f"🔇 {u.mention} muted for Bio-Link warning 3/3.")
                else:
                    await message.reply(f"⚠️ {u.mention}, Bio links allow nahi hain! ({BIO_WARNS[u.id]}/3)")

            if any(word in name for word in BAD_WORDS) or any(word in bio for word in BAD_WORDS):
                await message.chat.ban_member(u.id)
                await message.reply_text(BAN_CARD.format(user=u.mention, user_id=u.id, reason="NSFW Bio/Name"))
        except Exception as e: print(f"❌ Join Speed Error: {e}")

@app.on_message(filters.group & ~filters.service)
async def hyper_guard(client, message: Message):
    if not message.from_user: return
    if message.photo or message.sticker or message.animation or message.video:
        try:
            path = await message.download(file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.delete() 
                member = await client.get_chat_member(message.chat.id, message.from_user.id)
                if member.status not in [member.status.ADMINISTRATOR, member.status.OWNER]:
                    await message.chat.ban_member(message.from_user.id)
                    # Background history wipe
                    asyncio.create_task(a1_turbo_cleanup(client, message.chat.id, message.from_user.id))
                    await message.reply_text(BAN_CARD.format(user=message.from_user.mention, user_id=message.from_user.id, reason="NSFW Media Detected"))
            if path and os.path.exists(path): os.remove(path)
        except: pass

print("🚀 A1 EXTREME SONIC UI (FIXED) IS LIVE...")
app.run()
