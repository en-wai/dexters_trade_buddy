import os
import re
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
import MetaTrader5 as mt5

# Load credentials from .env
load_dotenv()
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")
login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")
mt5_path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"

# Update with your Telegram user ID
CONFIRMATION_USER_ID = 123456789  # <-- Replace with your own Telegram ID from @userinfobot

# Channel to listen to
channel_id = -1001196656830  # KOJOFOREX EXNESS VIP

# Log files
CSV_LOG_FILE = "trade_log.csv"
RETRY_FILE = "retry_queue.json"

# Initialize MT5
def init_mt5():
    if not mt5.initialize(path=mt5_path, login=login, password=password, server=server):
        print("❌ MT5 initialization failed:", mt5.last_error())
        return False
    return True

# Parse trade signal from message
def parse_signal(text):
    pattern = r'(BUY|SELL)\s+([A-Z]+)\s+@\s+([\d.]+).*?TP1[: ]([\d.]+).*?TP2[: ]([\d.]+).*?SL[: ]([\d.]+)'
    match = re.search(pattern, text.replace('\n', ' '))
    if match:
        return {
            'direction': match.group(1),
            'symbol': match.group(2),
            'entry': float(match.group(3)),
            'tp1': float(match.group(4)),
            'tp2': float(match.group(5)),
            'sl': float(match.group(6)),
        }
    return None

# Place trade in MT5
def place_trade(signal):
    symbol = signal["symbol"]
    lot = 0.1

    if not mt5.symbol_select(symbol, True):
        return False, "Symbol not in Market Watch"

    info = mt5.symbol_info(symbol)
    if info is None:
        return False, "Symbol info not found"

    point = info.point
    min_stop_distance = 30 * point

    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if signal["direction"] == "BUY" else tick.bid if tick else signal["entry"]

    if signal["direction"] == "BUY":
        if signal["tp1"] <= price or signal["sl"] >= price:
            return False, "Invalid TP/SL for BUY"
    else:
        if signal["tp1"] >= price or signal["sl"] <= price:
            return False, "Invalid TP/SL for SELL"

    if abs(price - signal["tp1"]) < min_stop_distance or abs(price - signal["sl"]) < min_stop_distance:
        return False, "TP/SL too close to price"

    order_type = mt5.ORDER_TYPE_BUY if signal["direction"] == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": signal["sl"],
        "tp": signal["tp1"],
        "deviation": 10,
        "magic": 123456,
        "comment": "Telegram Signal Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        queue_failed_trade(signal)
        return False, f"Trade failed: {result.retcode}"
    return True, f"Trade placed: {result.order}"

# Save signal to retry queue
def queue_failed_trade(signal):
    try:
        data = []
        if os.path.exists(RETRY_FILE):
            with open(RETRY_FILE, "r") as f:
                data = json.load(f)
        data.append(signal)
        with open(RETRY_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("⚠️ Trade added to retry queue.")
    except Exception as e:
        print(f"❌ Failed to save to retry queue: {e}")

# Log trade result
def log_trade(signal, result_msg):
    with open(CSV_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            signal["direction"],
            signal["symbol"],
            signal["entry"],
            signal["tp1"],
            signal["tp2"],
            signal["sl"],
            result_msg
        ])

# Start Telegram client
client = TelegramClient('session', api_id, api_hash)

@client.on(events.NewMessage(chats=channel_id))
async def handler(event):
    print(f"\n📩 New message at {datetime.now().strftime('%H:%M:%S')}")

    if not event.text:
        return

    signal = parse_signal(event.text)
    if signal:
        print(f"📊 Signal detected: {signal['direction']} {signal['symbol']}")

        if not init_mt5():
            await client.send_message(CONFIRMATION_USER_ID, "❌ MT5 login failed.")
            return

        success, result_msg = place_trade(signal)
        log_trade(signal, result_msg)

        # Build Telegram confirmation message
        if success:
            confirm_msg = (
                f"✅ {signal['direction']} {signal['symbol']} placed @ {signal['entry']}\n"
                f"🎯 SL: {signal['sl']} | TP1: {signal['tp1']}"
            )
        else:
            confirm_msg = f"❌ Trade failed for {signal['symbol']}: {result_msg}"

        await client.send_message(CONFIRMATION_USER_ID, confirm_msg)
        print(confirm_msg)

        mt5.shutdown()
    else:
        print("⏭ Not a trade signal.")

# Run the listener
with client:
    print("🟢 Listening for KOJOFOREX signals...")
    client.run_until_disconnected()
