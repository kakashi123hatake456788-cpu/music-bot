import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from yt_dlp import YoutubeDL
from fastapi import FastAPI
import uvicorn

# 1. Environment Variables Configuration
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# 2. FastAPI Setup (Keep-Alive Server for Render)
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Bot is running..."}

# 3. Telegram Client Initializations
bot = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(user_app)

# Helper function to extract direct stream link using yt-dlp
def extract_stream_url(query: str) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'auto',
    }
    with YoutubeDL(ydl_opts) as ydl:
        search_query = query if query.startswith("http") else f"ytsearch:{query}"
        info = ydl.extract_info(search_query, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            info = info['entries'][0]
        return info['url']

# Command: /play <song name or link>
@bot.on_message(filters.command("play") & filters.group)
async def play_music(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: /play <song name or YouTube link>")
        return

    query = " ".join(message.command[1:])
    status_msg = await message.reply_text(f"🔎 Searching for: {query}...")

    try:
        # Run yt-dlp in a non-blocking thread pool
        loop = asyncio.get_event_loop()
        stream_url = await loop.run_in_executor(None, extract_stream_url, query)

        # Stream directly into Telegram Voice Chat via PyTgCalls & FFmpeg
        await call_py.play(
            message.chat.id,
            MediaStream(stream_url)
        )
        await status_msg.edit_text(f"🎶 Now Playing: {query}")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}\n\n*Make sure Voice Chat is active and User Account is in the group.*")

# Command: /stop
@bot.on_message(filters.command("stop") & filters.group)
async def stop_music(client, message):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply_text("⏹️ Playback stopped.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# Service Runner
async def main():
    # Start Telegram Clients
    await user_app.start()
    await bot.start()
    await call_py.start()
    
    print(">>> Music Bot & PyTgCalls Started Successfully! <<<")

    # Start FastAPI Web Server on Render's assigned port
    port = int(os.environ.get("PORT", 10000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    await server.serve()

if name == "main":
    asyncio.run(main())
