import os
import re
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel

# Load .env config
load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

client = TelegramClient('session', api_id, api_hash)

def parse_signal(message_text):
    """
    Parses trade signal in the format:
    BUY XAUUSD @ 3215.56
    TP1:3222.39
    TP2:3232.12
    SL:3208.51
    """
    pattern = r'(BUY|SELL)\s+([A-Z]+)\s+@\s+([\d.]+)\s+TP1:([\d.]+)\s+TP2:([\d.]+)\s+SL:([\d.]+)'
    match = re.search(pattern, message_text.replace('\n', ' '))
    if match:
        return {
            'direction': match.group(1),
            'symbol': match.group(2),
            'entry': float(match.group(3)),
            'tp1': float(match.group(4)),
            'tp2': float(match.group(5)),
            'sl': float(match.group(6))
        }
    return None

async def main():
    await client.start(phone)

    channel = await client.get_entity(PeerChannel(-1001196656830))

    print(f"\n🔍 Checking for trade signals in: {channel.title}\n{'-' * 40}")
    async for message in client.iter_messages(channel, limit=20):
        if message.text:
            signal = parse_signal(message.text)
            if signal:
                print("✅ Parsed Signal:")
                for k, v in signal.items():
                    print(f"{k.capitalize()}: {v}")
                print("-" * 40)

with client:
    client.loop.run_until_complete(main())

