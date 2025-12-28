# Crypto Trading Bot

A modular Crypto Trading Bot for Bybit (USDT pairs) using a trend-following H4 strategy.

## Features
- **Strategy**: EMA 200 + EMA 55/10 Cross + MACD.
- **Risk Management**: 1% Risk per trade, ATR-based Stop Loss, 3 TP levels.
- **Virtual Execution**: Runs with virtual capital ($1000 default).
- **Notifications**: Telegram alerts for Entry, TP, and SL.

## Setup

### 1. Install Dependencies
The bot requires Python 3.8+ and the following libraries:
```bash
pip install -r requirements.txt
```
*Note: If `pip` is not found, you may need to install it (e.g., `sudo apt install python3-pip`) or install packages via your system package manager.*

### 2. Configuration
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
nano .env
```
- **Bybit Keys**: Required for fetching data (even for virtual trading).
- **Telegram**: Required for notifications.

### 3. Run the Bot
```bash
python3 main.py
```

## Structure
- `config.py`: Settings (Risk, Timeframe, etc.).
- `data/`: Market data fetching.
- `strategy/`: Strategy logic (Indicators, Signals).
- `execution/`: Virtual position management.
- `logs/`: Trade history (CSV) and logs.

## Logs
- Trades are logged to `logs/trade_history.csv`.
- Application logs are in `logs/crypto_bot.log`.
