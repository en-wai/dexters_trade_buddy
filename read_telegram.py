import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel

# Load credentials from .env
load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

client = TelegramClient('session', api_id, api_hash)

async def main():
    await client.start(phone)

    # Use the numeric channel ID (-100...) to get the entity
    channel = await client.get_entity(PeerChannel(-1001196656830))

    print(f"\n📥 Latest messages from: {channel.title}\n{'-' * 40}")
    async for message in client.iter_messages(channel, limit=10):
        if message.text:
            print(message.text)
            print('-' * 40)

with client:
    client.loop.run_until_complete(main())
