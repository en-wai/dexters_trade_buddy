import os
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Load your Telegram API credentials
load_dotenv()
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

# Start client session
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage())
async def debug_all(event):
    print("\n🔔 NEW MESSAGE RECEIVED")
    print(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📡 Chat ID: {event.chat_id}")
    print(f"👤 Sender: {getattr(event.sender, 'username', 'N/A')}")
    print(f"📝 Text: {event.text}\n")

# Run
with client:
    print("🟢 Listening to all incoming messages (any chat/channel)...")
    client.run_until_disconnected()

