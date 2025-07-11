# -*- coding: utf-8 -*-

import os
import time
import random
import asyncio
import yt_dlp
import datetime
from typing import Dict, List, Tuple, Union
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery
)
from pyrogram.errors import (
    UserAlreadyParticipant, UserNotParticipant,
    ChatAdminRequired, PeerIdInvalid
)
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputAudioStream, InputStream
from pytgcalls.types.input_stream import InputVideoStream
from config import (
    API_ID, API_HASH, BOT_TOKEN,
    SESSION_STRING, OWNER_ID
)

# Initialize Clients
app = Client(
    "MusicBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_bot = Client(
    SESSION_STRING,
    api_id=API_ID,
    api_hash=API_HASH
)

pytgcalls = PyTgCalls(user_bot)

# Global Variables
CHAT_INFO = {}
SONG_STATUS = {}
LOOP_MODE = {}
SLEEP_TIME = {}
SPAM_FLAG = {}
MUTED_USERS = {}
BANNED_USERS = {}
WELCOME_MSG = True
AUTO_REPLY = True

# Welcome Messages (Shayari)
WELCOME_SHAYARI = [
    "✨ Welcome to our group! ✨\nMain hoon tumhara sathi,\nTum mujhse bhula na paoge!",
    "🌹 Har koi naam hai tumhara,\nBahut khush hue hain hum tumhe pakar!",
    "🌸 Aaj bahar aai hai,\nTumhe dekh ke humare dil muskurai hai!",
    "💫 Tum jese aae ho,\nHumare group ki roonak mehko bhar aai ho!",
    "🌼 Welcome Dost, khush raho,\nYahan har pal music sath raho!"
]

# Auto Reply Messages (Girlfriend Style)
AUTO_REPLY_MESSAGES = [
    "Hmm... Mujhe bhi tumhara sath rehna achha lagta hai 😊",
    "Kya aap mujhe miss kar rahe ho? 🥺",
    "Hehe... Mera bhi mann kar raha hai tumse baat karne ka 😉",
    "Aaj tum bahut cute lag rahe ho! ❤️",
    "Kya aapne music sunna chaha hai? Mujhe bhi play kar lo na 😘"
]

# Admin Commands
@app.on_message(filters.command(["ban", "unban", "kick", "mute", "unmute"]) & filters.group)
async def admin_commands(client: Client, message: Message):
    user = await check_user(message)
    if not user:
        return
    
    command = message.command[0]
    admin = await is_admin(message)
    if not admin:
        await message.reply("You need to be admin to use this command!")
        return
    
    if command == "ban":
        if user.id in BANNED_USERS:
            await message.reply("User is already banned!")
            return
        BANNED_USERS[user.id] = True
        await message.chat.ban_member(user.id)
        await message.reply(f"🚫 User {user.mention} has been banned!")
    
    elif command == "unban":
        if user.id not in BANNED_USERS:
            await message.reply("User is not banned!")
            return
        BANNED_USERS.pop(user.id)
        await message.chat.unban_member(user.id)
        await message.reply(f"✅ User {user.mention} has been unbanned!")
    
    elif command == "kick":
        await message.chat.ban_member(user.id)
        await message.chat.unban_member(user.id)
        await message.reply(f"👢 User {user.mention} has been kicked!")
    
    elif command == "mute":
        if user.id in MUTED_USERS:
            await message.reply("User is already muted!")
            return
        MUTED_USERS[user.id] = True
        await message.reply(f"🔇 User {user.mention} has been muted!")
    
    elif command == "unmute":
        if user.id not in MUTED_USERS:
            await message.reply("User is not muted!")
            return
        MUTED_USERS.pop(user.id)
        await message.reply(f"🔊 User {user.mention} has been unmuted!")

# Spam Message Command
@app.on_message(filters.command("spam") & filters.user(OWNER_ID))
async def spam_message(client: Client, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: /spam [count] [message]")
        return
    
    count = int(message.command[1])
    message_text = " ".join(message.command[2:])
    
    if count > 20:
        await message.reply("Maximum 20 messages allowed!")
        return
    
    SPAM_FLAG[message.chat.id] = True
    for _ in range(count):
        if not SPAM_FLAG.get(message.chat.id):
            break
        await message.reply(message_text)
        await asyncio.sleep(0.5)
    
    SPAM_FLAG.pop(message.chat.id, None)

# Stop Spam Command
@app.on_message(filters.command("stopspam") & filters.user(OWNER_ID))
async def stop_spam(client: Client, message: Message):
    if message.chat.id in SPAM_FLAG:
        SPAM_FLAG.pop(message.chat.id)
        await message.reply("Spam stopped!")
    else:
        await message.reply("No active spam to stop!")

# Auto Reply to Messages
@app.on_message(filters.group & ~filters.command & ~filters.edited)
async def auto_reply(client: Client, message: Message):
    if not AUTO_REPLY or message.from_user.is_bot:
        return
    
    if random.random() < 0.3:  # 30% chance to reply
        reply = random.choice(AUTO_REPLY_MESSAGES)
        await message.reply(reply)

# Welcome New Members
@app.on_message(filters.new_chat_members & filters.group)
async def welcome_new_members(client: Client, message: Message):
    if not WELCOME_MSG:
        return
    
    for user in message.new_chat_members:
        shayari = random.choice(WELCOME_SHAYARI)
        await message.reply(f"👋 {user.mention}\n{shayari}")

# Broadcast Message to All Groups
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast [message]")
        return
    
    message_text = " ".join(message.command[1:])
    chats = await client.get_dialogs()
    
    for chat in chats:
        if chat.chat.type in ["group", "supergroup"]:
            try:
                await client.send_message(
                    chat.chat.id,
                    f"📢 Broadcast Message:\n\n{message_text}"
                )
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to broadcast in {chat.chat.id}: {e}")
    
    await message.reply("Broadcast completed!")

# Music Player Functions
async def download_content(yt_url: str) -> Tuple[str, Dict]:
    options = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }],
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        info = await asyncio.to_thread(ydl.extract_info, yt_url, download=True)
        file = ydl.prepare_filename(info)
    
    return file, info

async def download_video(yt_url: str, quality: str = "1080") -> Tuple[str, Dict]:
    options = {
        "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
        "outtmpl": "downloads/%(id)s.%(ext)s",
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        info = await asyncio.to_thread(ydl.extract_info, yt_url, download=True)
        file = ydl.prepare_filename(info)
    
    return file, info

# Play Command
@app.on_message(filters.command("play") & filters.group)
async def play_music(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /play [song name/YouTube URL]")
        return
    
    query = " ".join(message.command[1:])
    chat_id = message.chat.id
    
    try:
        await message.reply("🔍 Searching...")
        
        if "youtube.com" in query or "youtu.be" in query:
            file, info = await download_content(query)
        else:
            file, info = await download_content(f"ytsearch:{query}")
        
        title = info.get("title", "Unknown Title")
        duration = info.get("duration", 0)
        thumb = info.get("thumbnail", "")
        
        # Join VC if not already joined
        try:
            await app.join_chat(chat_id)
        except UserAlreadyParticipant:
            pass
        
        # Play the audio
        await pytgcalls.join_group_call(
            chat_id,
            InputStream(
                InputAudioStream(
                    file,
                ),
            ),
        )
        
        # Save song status
        SONG_STATUS[chat_id] = {
            "title": title,
            "duration": duration,
            "start_time": time.time(),
            "chat_id": chat_id,
            "file": file
        }
        
        # Send playing message with progress bar
        msg = await message.reply_photo(
            thumb,
            caption=(
                f"🎵 Now Playing: {title}\n"
                f"⏳ Duration: {duration} seconds\n"
                f"🎭 Requested by: {message.from_user.mention}"
            ),
            reply_markup=progress_bar(0)
        )
        
        # Update progress bar
        CHAT_INFO[chat_id] = {"message": msg, "last_update": time.time()}
        
    except Exception as e:
        await message.reply(f"Error: {e}")

# Video Play Command
@app.on_message(filters.command("vplay") & filters.group)
async def play_video(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /vplay [video name/YouTube URL] [quality]")
        return
    
    query = message.command[1]
    quality = "1080"  # Default quality
    
    if len(message.command) > 2:
        quality = message.command[2]
    
    chat_id = message.chat.id
    
    try:
        await message.reply("🔍 Searching...")
        
        if "youtube.com" in query or "youtu.be" in query:
            file, info = await download_video(query, quality)
        else:
            file, info = await download_video(f"ytsearch:{query}", quality)
        
        title = info.get("title", "Unknown Title")
        duration = info.get("duration", 0)
        thumb = info.get("thumbnail", "")
        
        # Join VC if not already joined
        try:
            await app.join_chat(chat_id)
        except UserAlreadyParticipant:
            pass
        
        # Play the video
        await pytgcalls.join_group_call(
            chat_id,
            InputStream(
                InputVideoStream(
                    file,
                ),
            ),
        )
        
        # Save song status
        SONG_STATUS[chat_id] = {
            "title": title,
            "duration": duration,
            "start_time": time.time(),
            "chat_id": chat_id,
            "file": file,
            "is_video": True
        }
        
        # Send playing message with progress bar
        msg = await message.reply_photo(
            thumb,
            caption=(
                f"🎬 Now Playing: {title}\n"
                f"⏳ Duration: {duration} seconds\n"
                f"🎭 Requested by: {message.from_user.mention}"
            ),
            reply_markup=progress_bar(0)
        )
        
        # Update progress bar
        CHAT_INFO[chat_id] = {"message": msg, "last_update": time.time()}
        
    except Exception as e:
        await message.reply(f"Error: {e}")

# Progress Bar Generator
def progress_bar(percent: int) -> InlineKeyboardMarkup:
    bar = "▬" * 10
    pos = int(percent / 10)
    bar = bar[:pos] + "🔘" + bar[pos+1:]
    
    keyboard = [
        [
            InlineKeyboardButton("⏮", callback_data="rewind"),
            InlineKeyboardButton("⏸", callback_data="pause"),
            InlineKeyboardButton("⏭", callback_data="forward"),
        ],
        [
            InlineKeyboardButton("🔁 Loop", callback_data="loop"),
            InlineKeyboardButton("🔇 Mute", callback_data="mute"),
            InlineKeyboardButton("🔊 Volume", callback_data="volume"),
        ],
        [
            InlineKeyboardButton(bar, callback_data="progress")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

# Volume Control Bar
def volume_bar(volume: int) -> InlineKeyboardMarkup:
    bar = "▬" * 10
    pos = int(volume / 10)
    bar = bar[:pos] + "🔘" + bar[pos+1:]
    
    keyboard = [
        [
            InlineKeyboardButton("🔈 -10", callback_data="vol_down"),
            InlineKeyboardButton("🔊 +10", callback_data="vol_up"),
        ],
        [
            InlineKeyboardButton(bar, callback_data="vol_bar")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

# Callback Query Handler
@app.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    data = callback.data
    
    if data == "close":
        await callback.message.delete()
        return
    
    if data == "back":
        if chat_id in SONG_STATUS:
            song = SONG_STATUS[chat_id]
            current_pos = int(time.time() - song["start_time"])
            percent = (current_pos / song["duration"]) * 100
            await callback.message.edit_reply_markup(progress_bar(percent))
        return
    
    if data == "volume":
        await callback.message.edit_reply_markup(volume_bar(50))
        return
    
    if data in ["vol_up", "vol_down"]:
        await callback.answer("Volume control will be implemented soon!")
        return
    
    if data == "loop":
        if chat_id in LOOP_MODE:
            LOOP_MODE.pop(chat_id)
            await callback.answer("Loop mode disabled!")
        else:
            LOOP_MODE[chat_id] = True
            await callback.answer("Loop mode enabled!")
        return
    
    if data == "pause":
        await callback.answer("Pause/resume will be implemented soon!")
        return
    
    if data in ["rewind", "forward"]:
        await callback.answer("Seek controls will be implemented soon!")
        return
    
    if data == "mute":
        await callback.answer("Mute controls will be implemented soon!")
        return

# Song Status Command
@app.on_message(filters.command("status") & filters.group)
async def song_status(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in SONG_STATUS:
        await message.reply("No song is currently playing!")
        return
    
    song = SONG_STATUS[chat_id]
    current_pos = int(time.time() - song["start_time"])
    percent = (current_pos / song["duration"]) * 100
    
    msg = await message.reply(
        f"🎵 Currently Playing: {song['title']}\n"
        f"⏳ Position: {current_pos}/{song['duration']} seconds\n"
        f"🔁 Loop: {'On' if chat_id in LOOP_MODE else 'Off'}",
        reply_markup=progress_bar(percent)
    )
    
    CHAT_INFO[chat_id] = {"message": msg, "last_update": time.time()}

# Skip Command
@app.on_message(filters.command("skip") & filters.group)
async def skip_song(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in SONG_STATUS:
        await message.reply("No song to skip!")
        return
    
    await pytgcalls.leave_group_call(chat_id)
    song = SONG_STATUS.pop(chat_id)
    
    try:
        os.remove(song["file"])
    except:
        pass
    
    await message.reply(f"⏩ Skipped: {song['title']}")

# Stop Command
@app.on_message(filters.command("stop") & filters.group)
async def stop_playback(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in SONG_STATUS:
        await message.reply("Nothing is playing!")
        return
    
    await pytgcalls.leave_group_call(chat_id)
    song = SONG_STATUS.pop(chat_id)
    
    try:
        os.remove(song["file"])
    except:
        pass
    
    await message.reply(f"⏹ Stopped playback: {song['title']}")

# Loop Command
@app.on_message(filters.command("loop") & filters.group)
async def loop_song(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in LOOP_MODE:
        LOOP_MODE.pop(chat_id)
        await message.reply("🔁 Loop mode disabled!")
    else:
        LOOP_MODE[chat_id] = True
        await message.reply("🔁 Loop mode enabled!")

# Sleep Command
@app.on_message(filters.command("sleep") & filters.group)
async def sleep_time(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /sleep [time in minutes]")
        return
    
    time_min = int(message.command[1])
    chat_id = message.chat.id
    SLEEP_TIME[chat_id] = time.time() + (time_min * 60)
    
    await message.reply(f"💤 Bot will sleep for {time_min} minutes!")

# Wake Command
@app.on_message(filters.command("wake") & filters.group)
async def wake_up(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in SLEEP_TIME:
        SLEEP_TIME.pop(chat_id)
        await message.reply("🌞 Bot is awake now!")
    else:
        await message.reply("Bot is already awake!")

# Song Recommendations
@app.on_message(filters.command("recommend") & filters.group)
async def recommend_songs(client: Client, message: Message):
    recommendations = [
        "Shape of You - Ed Sheeran",
        "Blinding Lights - The Weeknd",
        "Dance Monkey - Tones and I",
        "Stay - The Kid LAROI, Justin Bieber",
        "Levitating - Dua Lipa",
        "Montero - Lil Nas X",
        "Peaches - Justin Bieber",
        "Save Your Tears - The Weeknd",
        "Good 4 U - Olivia Rodrigo",
        "Butter - BTS"
    ]
    
    recommendation_text = "🎧 Recommended Songs:\n\n" + "\n".join(
        f"▸ {song}" for song in random.sample(recommendations, 5)
    )
    
    await message.reply(recommendation_text)

# Help Command
@app.on_message(filters.command("help"))
async def help_menu(client: Client, message: Message):
    help_text = """
🎵 Music Bot Help Menu 🎵

🎧 Music Commands:
▸ /play [song name/URL] - Play song
▸ /vplay [video name/URL] - Play video
▸ /skip - Skip current song
▸ /stop - Stop playback
▸ /loop - Toggle loop mode
▸ /status - Show current song status
▸ /recommend - Get song recommendations

⏳ Sleep Mode:
▸ /sleep [minutes] - Sleep the bot
▸ /wake - Wake up the bot

👮 Admin Commands:
▸ /ban [reply/username] - Ban user
▸ /unban [reply/username] - Unban user
▸ /kick [reply/username] - Kick user
▸ /mute [reply/username] - Mute user
▸ /unmute [reply/username] - Unmute user
▸ /broadcast [message] - Broadcast message
▸ /spam [count] [message] - Spam message
▸ /stopspam - Stop spam

💬 Auto Reply:
▸ /autoreply [on/off] - Toggle auto reply
▸ /welcome [on/off] - Toggle welcome messages
"""
    await message.reply(help_text)

# Auto Reply Toggle
@app.on_message(filters.command("autoreply") & filters.user(OWNER_ID))
async def toggle_auto_reply(client: Client, message: Message):
    global AUTO_REPLY
    if len(message.command) < 2:
        AUTO_REPLY = not AUTO_REPLY
    else:
        AUTO_REPLY = message.command[1].lower() in ["on", "yes", "true"]
    
    await message.reply(f"Auto Reply: {'On' if AUTO_REPLY else 'Off'}")

# Welcome Message Toggle
@app.on_message(filters.command("welcome") & filters.user(OWNER_ID))
async def toggle_welcome(client: Client, message: Message):
    global WELCOME_MSG
    if len(message.command) < 2:
        WELCOME_MSG = not WELCOME_MSG
    else:
        WELCOME_MSG = message.command[1].lower() in ["on", "yes", "true"]
    
    await message.reply(f"Welcome Messages: {'On' if WELCOME_MSG else 'Off'}")

# Helper Functions
async def check_user(message: Message) -> Union[None, User]:
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            return await app.get_users(message.command[1])
        except PeerIdInvalid:
            await message.reply("Invalid user!")
            return None
    else:
        await message.reply("Reply to a user or provide username!")
        return None

async def is_admin(message: Message) -> bool:
    if message.from_user.id == OWNER_ID:
        return True
    
    try:
        user = await message.chat.get_member(message.from_user.id)
        return user.privileges.can_restrict_members
    except:
        return False

# Update Progress Bar Periodically
async def update_progress_bar():
    while True:
        await asyncio.sleep(5)
        for chat_id, info in list(CHAT_INFO.items()):
            if time.time() - info["last_update"] < 5:
                continue
            
            if chat_id not in SONG_STATUS:
                try:
                    await info["message"].delete()
                except:
                    pass
                CHAT_INFO.pop(chat_id)
                continue
            
            song = SONG_STATUS[chat_id]
            current_pos = int(time.time() - song["start_time"])
            
            if current_pos > song["duration"]:
                if chat_id in LOOP_MODE:
                    # Restart the song if in loop mode
                    song["start_time"] = time.time()
                    CHAT_INFO[chat_id]["last_update"] = time.time()
                    continue
                else:
                    # Song finished, clean up
                    try:
                        await pytgcalls.leave_group_call(chat_id)
                        os.remove(song["file"])
                    except:
                        pass
                    SONG_STATUS.pop(chat_id)
                    try:
                        await info["message"].delete()
                    except:
                        pass
                    CHAT_INFO.pop(chat_id)
                    continue
            
            percent = (current_pos / song["duration"]) * 100
            try:
                await info["message"].edit_reply_markup(progress_bar(percent))
                CHAT_INFO[chat_id]["last_update"] = time.time()
            except:
                pass

# Start the Bot
async def start_bot():
    await app.start()
    await user_bot.start()
    await pytgcalls.start()
    asyncio.create_task(update_progress_bar())
    print("Bot started!")

if __name__ == "__main__":
    # Create downloads directory if not exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    # Run the bot
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
    loop.run_forever()