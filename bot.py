import os, requests, re, cv2, asyncio, zipfile, shutil, random
from PIL import Image
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

# --- CONFIGURATION (Bhai dhyan se bharna) ---
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
GBAN_LIST = set()

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTIMATE_GOD_MODE", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UI DESIGNS ---

DM_START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ɢᴜᴀʀᴅɪᴀɴ**
Status: `Turbo God Mode Active` 🚀
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
🛠️ **Action:** `Full History Wipe + Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE TURBO FUNCTIONS ---

async def a1_turbo_cleanup(client, chat_id, user_id):
    """Background parallel history wipe (500 Limit)"""
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
        print("❌ Supergroup settings required for history cleanup!")
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
        if res.get('status') == 'success' and (res['nudity']['sexual_display'] > 0.10 or res['nudity']['erotica'] > 0.10):
            return True
    except: pass
    return False

# --- HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start_dm(client, message):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")]])
    await message.reply_text(DM_START_TEXT, reply_markup=buttons)

@app.on_message(filters.command("scan") & filters.group)
async def extreme_scan(client, message):
    progress = await message.reply("🔎 **Scanning group for NSFW content (500 Limit)...**")
    count = 0
    try:
        async for msg in client.get_chat_history(message.chat.id, limit=500):
            if msg.photo or msg.sticker or msg.animation:
                path = await msg.download(file_name=DOWNLOAD_DIR)
                if check_nsfw(path):
                    await msg.delete(); count += 1
                if os.path.exists(path): os.remove(path)
        await progress.edit(f"✅ **Scan Complete!** {count} items removed.")
    except errors.BotMethodInvalid:
        await progress.edit("❌ **Error:** Scan feature requires **Supergroup** settings!")

@app.on_message(filters.group & filters.new_chat_members)
async def extreme_join_guard(client, message: Message):
    for u in message.new_chat_members:
        try:
            # 1. PFP Scan
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
            full_user = await client.get_chat(u.id) # Correct method for bio fix
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
        except Exception as e: print(f"❌ Join Scan Error: {e}")

@app.on_message(filters.group & ~filters.service)
async def hyper_guard(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    if u_id in GBAN_LIST: await message.chat.ban_member(u_id); await message.delete(); return

    if message.photo or message.sticker or message.animation or message.video or message.document:
        try:
            path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False
            if message.document and message.document.file_name.endswith('.zip'):
                with zipfile.ZipFile(path, 'r') as zf:
                    z_tmp = f"{DOWNLOAD_DIR}unzip_{message.id}"; zf.extractall(z_tmp)
                    for r, _, files in os.walk(z_tmp):
                        for f in files:
                            if f.lower().endswith(('.jpg', '.png', '.webp')) and check_nsfw(os.path.join(r, f)):
                                is_bad = True; break
                    shutil.rmtree(z_tmp)
            else: is_bad = check_nsfw(path)

            if is_bad:
                await message.delete() 
                member = await client.get_chat_member(message.chat.id, u_id)
                if member.status not in [member.status.ADMINISTRATOR, member.status.OWNER]:
                    await message.chat.ban_member(u_id)
                    asyncio.create_task(a1_turbo_cleanup(client, message.chat.id, u_id))
                    await message.reply_text(BAN_CARD.format(user=message.from_user.mention, user_id=u_id, reason="NSFW Media Detected"))
            if path and os.path.exists(path): os.remove(path)
        except: pass

@app.on_message(filters.command("gban") & filters.user(SUDO_USERS))
async def gban_cmd(client, message):
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    GBAN_LIST.add(uid); await message.chat.ban_member(uid); await message.reply("🚫 **Global Ban Active!**")

print("🚀 A1 FINAL ABSOLUTE GOD MODE IS LIVE...")
app.run()
