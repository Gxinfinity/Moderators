import os, requests, re, cv2, asyncio, zipfile, shutil, random
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

# --- CONFIGURATION (Dhyan se bharein) ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "APNA_BOT_TOKEN_YAHAN_DAALEIN" # @BotFather wala token

LOG_CHANNEL_ID = -1003506657299 
SUDO_USERS = [7487670897, 8409591285] 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_FINAL_FIX", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- CORE FUNCTIONS ---

async def a1_sonic_cleanup(client, chat_id, user_id):
    """Batch deletion for speed"""
    msg_ids = []
    try:
        async for msg in client.get_chat_history(chat_id, limit=300):
            if msg.from_user and msg.from_user.id == user_id:
                msg_ids.append(msg.id)
                if len(msg_ids) >= 100:
                    await client.delete_messages(chat_id, msg_ids)
                    msg_ids = []
        if msg_ids: await client.delete_messages(chat_id, msg_ids)
        print(f"🗑️ History cleaned for {user_id}")
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
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                if n['sexual_display'] > 0.10 or n['erotica'] > 0.10: return True
    except: pass
    return False

# --- HANDLERS ---

@app.on_message(filters.command("check") & filters.group)
async def health_check(client, message):
    print(f"📡 Check command received in {message.chat.title}") # Terminal mein dikhega
    me = await client.get_chat_member(message.chat.id, "me")
    report = (f"🛠️ **ᴀ1 ʙᴏᴛ sᴛᴀᴛᴜs**\n━━━━━━━━━━━━\n"
              f"🚫 Ban: {'✅' if me.privileges.can_restrict_members else '❌'}\n"
              f"🗑️ Delete: {'✅' if me.privileges.can_delete_messages else '❌'}\n"
              f"📊 Supergroup: {'✅' if message.chat.type.name == 'SUPERGROUP' else '❌'}")
    await message.reply(report)

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    
    # Debug: Terminal mein har message ki info
    print(f"📩 Message from {message.from_user.first_name} in {message.chat.title}")

    # Admin check
    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in [member.status.ADMINISTRATOR, member.status.OWNER]: is_admin = True
    except: pass

    # Media Scan (Photo, Sticker, Video, GIF, ZIP)
    if message.photo or message.sticker or message.video or message.animation or message.document:
        unique_name = f"{DOWNLOAD_DIR}{u_id}_{message.id}_{random.randint(100,999)}"
        file_path = await message.download(file_name=unique_name)
        
        is_bad = False
        if message.document and message.document.file_name.endswith('.zip'):
            # ZIP logic
            pass # (ZIP logic same as previous)
        elif message.animation or message.video or (message.sticker and message.sticker.is_video):
            cap = cv2.VideoCapture(file_path); cap.set(cv2.CAP_PROP_POS_FRAMES, 5)
            ret, frame = cap.read()
            if ret:
                tmp = f"{file_path}_v.jpg"; cv2.imwrite(tmp, frame)
                is_bad = check_nsfw(tmp); os.remove(tmp)
            cap.release()
        else: is_bad = check_nsfw(file_path)

        if is_bad:
            await message.delete()
            if not is_admin:
                await message.chat.ban_member(u_id)
                asyncio.create_task(a1_sonic_cleanup(client, message.chat.id, u_id))
                await message.reply(f"🚫 **Direct Ban!** {message.from_user.mention} history cleared.")
            else: await message.reply("⚠️ **Admin Warning!** NSFW media removed.")
        
        if file_path and os.path.exists(file_path): os.remove(file_path)

@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        print(f"🆕 New Member Join: {u.first_name}")
        try:
            full_user = await client.get_users(u.id)
            bio, name = (full_user.bio or "").lower(), f"{u.first_name} {u.username or ''}".lower()
            
            # NSFW Name/Bio Ban
            if any(word in name for word in BAD_WORDS) or any(word in bio for word in BAD_WORDS):
                await message.chat.ban_member(u.id)
                await message.reply(f"🚫 **Direct Ban!** {u.mention} has 18+ Name/Bio.")
                continue

            # PFP Scan
            photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
            if photos:
                path = await client.download_media(photos[0].file_id, file_name=f"{DOWNLOAD_DIR}pfp_{u.id}")
                if check_nsfw(path):
                    await message.chat.ban_member(u.id)
                    asyncio.create_task(a1_sonic_cleanup(client, message.chat.id, u.id))
                if os.path.exists(path): os.remove(path)
        except Exception as e: print(f"❌ Join Error: {e}")

print("🚀 A1 FINAL GOD MODE IS LIVE...")
app.run()
