import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")
terminal_path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"  # Update if needed

# Initialize MT5
if not mt5.initialize(path=terminal_path, login=login, password=password, server=server):
    print("❌ Initialization failed:", mt5.last_error())
    quit()

# Example signal (edit as needed or feed from Telegram)
signal = {
    "direction": "BUY",  # or "SELL"
    "symbol": "XAUUSDm",  # Ensure this matches Market Watch
    "entry": 3228.00,
    "tp1": 3235.00,
    "tp2": 3245.00,
    "sl": 3220.00
}

symbol = signal["symbol"]
lot = 0.1  # Adjust based on your demo balance

# Ensure symbol is visible
if not mt5.symbol_select(symbol, True):
    print(f"❌ Symbol {symbol} is not available in Market Watch.")
    mt5.shutdown()
    quit()

# Get symbol info
info = mt5.symbol_info(symbol)
if info is None:
    print(f"❌ Could not retrieve info for {symbol}")
    mt5.shutdown()
    quit()

# Set up price and fallback if market is closed
tick = mt5.symbol_info_tick(symbol)
if tick is None:
    print(f"⚠️ Market closed or no live price. Using entry price.")
    price = signal["entry"]
else:
    price = tick.ask if signal["direction"] == "BUY" else tick.bid

# Safety margin for SL/TP distance
point = info.point
min_stop_distance = 30 * point  # Fallback if broker doesn’t expose stops_level

# Validate direction of TP/SL
if signal["direction"] == "BUY":
    if signal["tp1"] <= price or signal["sl"] >= price:
        print(f"⚠️ Invalid TP or SL for BUY. TP must be > price and SL < price.")
        mt5.shutdown()
        quit()
else:
    if signal["tp1"] >= price or signal["sl"] <= price:
        print(f"⚠️ Invalid TP or SL for SELL. TP must be < price and SL > price.")
        mt5.shutdown()
        quit()

# Validate TP/SL distance
if abs(price - signal["tp1"]) < min_stop_distance or abs(price - signal["sl"]) < min_stop_distance:
    print(f"⚠️ TP or SL too close to price. Must be at least {min_stop_distance:.5f} away.")
    mt5.shutdown()
    quit()

# Define order type
order_type = mt5.ORDER_TYPE_BUY if signal["direction"] == "BUY" else mt5.ORDER_TYPE_SELL

# Prepare trade request
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

# Send the order
result = mt5.order_send(request)

# Evaluate result
if result.retcode != mt5.TRADE_RETCODE_DONE:
    print(f"❌ Trade failed. Code: {result.retcode}")
    print(f"🛠 Error details: {result}")
else:
    print("✅ Trade placed successfully!")
    print(f"🎟 Ticket: {result.order}, Price: {result.price}")
    print(f"📉 SL: {signal['sl']}, 📈 TP: {signal['tp1']}")


# Shutdown
mt5.shutdown()
