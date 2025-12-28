import requests
from crypto_bot.config import Config
from crypto_bot.utils.logger import setup_logger

logger = setup_logger("Notifier")

class TelegramNotifier:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
    def send_message(self, message):
        """
        Send a message to the configured Telegram chat.
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram token or chat_id not set. Notification skipped.")
            return

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            
    def notify_entry(self, symbol, trade_params):
        msg = (
            f"🚀 **ENTRY TRIGGERED**\n"
            f"Symbol: `{symbol}`\n"
            f"Excecuting at: `{trade_params['entry_price']}`\n"
            f"Size: `{trade_params['size']:.4f}`\n"
            f"Stop Loss: `{trade_params['stop_loss']:.4f}`\n"
            f"TP1: `{trade_params['tp1']:.4f}` | TP2: `{trade_params['tp2']:.4f}` | TP3: `{trade_params['tp3']:.4f}`"
        )
        self.send_message(msg)
        
    def notify_tp(self, symbol, tp_level, price):
        msg = f"💰 **TAKE PROFIT {tp_level} HIT**\nSymbol: `{symbol}`\nPrice: `{price}`"
        self.send_message(msg)
        
    def notify_sl(self, symbol, price):
        msg = f"🛑 **STOP LOSS HIT**\nSymbol: `{symbol}`\nPrice: `{price}`"
        self.send_message(msg)
