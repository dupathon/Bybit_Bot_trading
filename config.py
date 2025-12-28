import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Bybit API
    BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
    BYBIT_SECRET_KEY = os.getenv("BYBIT_SECRET_KEY")
    
    # Trading Settings
    TIMEFRAME = '4h'
    SYMBOL_TYPE = 'future'  # or 'spot' - usually bots trade futures for shorting, user asked for USDT pairs, likely spot or futures. 
                            # User mentioned "Trend-following with 2 positions maximum", usually implies leverage/margin or just spot.
                            # "USDT pairs" usually implies Futures if shorting is needed, strategies involve "bullish" and "bearish".
                            # User said "Price below EMA 200 -> bearish -> skip buy".
                            # This implies ONLY LONG positions ("skip buy"). So Spot or Futures Long-Only.
                            # Let's default to Spot for safety, but make it configurable.
    
    # Strategy Settings
    MAX_OPEN_POSITIONS = 2
    RISK_PER_TRADE_PERCENT = 0.01  # 1%
    MAX_DAILY_LOSS_PERCENT = 0.03  # 3%
    VIRTUAL_CAPITAL = 1000.0
    
    # Indicators
    EMA_LONG = 200
    EMA_MEDIUM = 55
    EMA_SHORT = 10
    ATR_PERIOD = 14
    ATR_MULTIPLIER = 2.0
    
    # Volume Filter
    MIN_DAILY_VOLUME_USDT = 1000000
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Paths
    PARAMS_FILE = 'trade_params.json'  # To store current state if needed
    LOG_FILE = 'logs/crypto_bot.log'
    CSV_FILE = 'logs/trade_history.csv'

    @staticmethod
    def validate():
        if not Config.BYBIT_API_KEY or not Config.BYBIT_SECRET_KEY:
            print("WARNING: Bybit API Keys not found in .env. Order execution will fail.")
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            print("WARNING: Telegram credentials not found. Notifications disabled.")
