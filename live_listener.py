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

# Your Telegram user ID
CONFIRMATION_USER_ID = 780015597

# Channels to monitor (mentor and test)
channel_ids = [-1001196656830, -1002515836973]

# Files
CSV_LOG_FILE = "trade_log.csv"
RETRY_FILE = "retry_queue.json"

# Map signal symbols to MT5 tradable symbols
SYMBOL_MAP = {
    "XAUUSD": "XAUUSDm",
    "NAS100": "NAS100m",
    "US30": "US30m",
    # Add more as needed
}

def init_mt5():
    if not mt5.initialize(path=mt5_path, login=login, password=password, server=server):
        print("❌ MT5 initialization failed:", mt5.last_error())
        return False
    return True

def parse_signal(text):
    text = ' '.join(text.replace('\n', ' ').replace('\r', '').split())
    pattern = (
        r'(?i)\b(BUY|SELL)\s+'
        r'([A-Z]{3,6}m?)\s*[@:\s]\s*([\d.]+)'
        r'.*?TP1[:\s]*([\d.]+)'
        r'.*?TP2[:\s]*([\d.]+)'
        r'.*?SL[:\s]*([\d.]+)'
    )
    match = re.search(pattern, text)
    if match:
        return {
            'direction': match.group(1).upper(),
            'symbol': match.group(2),
            'entry': float(match.group(3)),
            'tp1': float(match.group(4)),
            'tp2': float(match.group(5)),
            'sl': float(match.group(6)),
        }
    return None

def place_trade(signal):
    symbol = SYMBOL_MAP.get(signal["symbol"], signal["symbol"])
    total_lot = 0.2
    lot_per_tp = round(total_lot / 2, 2)

    if not mt5.symbol_select(symbol, True):
        return False, f"Symbol {symbol} not in Market Watch"

    info = mt5.symbol_info(symbol)
    if info is None:
        return False, f"Symbol info not found for {symbol}"

    point = info.point
    min_stop_distance = 30 * point

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return False, "No market price available"

    price = tick.ask if signal["direction"] == "BUY" else tick.bid

    if signal["direction"] == "BUY":
        if signal["tp1"] <= price or signal["tp2"] <= price or signal["sl"] >= price:
            return False, "Invalid TP/SL for BUY"
    else:
        if signal["tp1"] >= price or signal["tp2"] >= price or signal["sl"] <= price:
            return False, "Invalid TP/SL for SELL"

    if any(abs(price - tp) < min_stop_distance for tp in [signal["tp1"], signal["tp2"]]) or abs(price - signal["sl"]) < min_stop_distance:
        return False, "TP or SL too close to price"

    order_type = mt5.ORDER_TYPE_BUY if signal["direction"] == "BUY" else mt5.ORDER_TYPE_SELL
    trade_results = []

    for tp in [signal["tp1"], signal["tp2"]]:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_per_tp,
            "type": order_type,
            "price": price,
            "sl": signal["sl"],
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": f"TP target: {tp}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            trade_results.append(f"✅ TP {tp} placed (Ticket {result.order})")
            log_trade(signal, f"TP {tp} - Success - Order {result.order}")
        else:
            trade_results.append(f"❌ TP {tp} failed (Code {result.retcode})")
            queue_failed_trade(signal)

    return True, "\n".join(trade_results)

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

def log_trade(signal, result_msg):
    with open(CSV_LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
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

client = TelegramClient('session', api_id, api_hash)

@client.on(events.NewMessage(chats=channel_ids))
async def handler(event):
    print(f"\n📩 New message received at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📡 Message received from chat ID: {event.chat_id}")

    if not event.text:
        return

    signal = parse_signal(event.text)
    if signal:
        print(f"📊 Signal detected: {signal['direction']} {signal['symbol']}")

        if not init_mt5():
            await client.send_message(CONFIRMATION_USER_ID, "❌ MT5 login failed.")
            return

        success, result_msg = place_trade(signal)
        confirm_msg = (
            f"✅ {signal['direction']} {signal['symbol']} placed @ {signal['entry']}\n"
            f"🎯 SL: {signal['sl']} | TP1: {signal['tp1']} | TP2: {signal['tp2']}\n"
            f"{result_msg}"
        ) if success else f"❌ Trade failed for {signal['symbol']}: {result_msg}"

        await client.send_message(CONFIRMATION_USER_ID, confirm_msg)
        print(confirm_msg)

        mt5.shutdown()
    else:
        print("⏭ Not a trade signal.")

with client:
    print("🟢 Bot is now listening for new messages...")
    client.run_until_disconnected()
