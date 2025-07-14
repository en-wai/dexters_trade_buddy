# Trade Buddy - Automated MT5 Trading and News Analysis Bot

Trade Buddy is a Python-based automation tool designed for traders. It connects MetaTrader 5 (MT5) with Telegram and OpenAI's GPT to automate trading decisions and simplify market news understanding.

---

## Features

- Automatically reads trading signals from Telegram.
- Places trades on MT5 (MetaTrader 5) automatically.
- Monitors MT5 news headlines.
- Uses ChatGPT (OpenAI) to explain market news in simple, beginner-friendly language.
- Sends news analysis directly to your Telegram.

---

## Project Structure

```
trade-buddy/
├── live_listener.py       # Main bot orchestrator
├── parse_signals.py
├── place_trade.py
├── read_telegram.py
├── news_analysis/         # News module
│   ├── news_listener.py
│   ├── analyze_news.py
│   ├── send_to_telegram.py
│   └── run_once.py
├── .env                   # Contains API keys (DO NOT SHARE)
├── .gitignore             # Ignore sensitive files
├── README.md
├── venv/                  # Python virtual environment
```

---

## Installation Guide

### 1. Setup Python Environment

1. Ensure Python is installed.
2. Open Command Prompt or terminal inside the project folder.
3. Run:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:

```bash
pip install openai python-telegram-bot telethon MetaTrader5 python-dotenv
```

---

### 2. Configure Environment Variables

1. Create a `.env` file in the project root folder.
2. Add the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

### 3. Setup Telegram Bot

1. Search @BotFather in Telegram.
2. Create a new bot and get the Bot Token.
3. Start the bot and retrieve your chat ID using: `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`

---

### 4. Running the Bot

- To start trading bot:

```bash
python live_listener.py
```

- To test the news analysis separately:

```bash
python news_analysis/run_once.py
```

---

## Disclaimer

- Use at your own risk.
- Always test with a demo account before using live funds.

---

## Support

For assistance, contact the developer or open an issue on the GitHub repository.

---

Happy Trading! 🚀

