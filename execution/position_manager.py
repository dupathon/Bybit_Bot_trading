import json
import os
import csv
from datetime import datetime
from crypto_bot.config import Config
from crypto_bot.utils.logger import setup_logger
from crypto_bot.telegram.notifier import TelegramNotifier

logger = setup_logger("PositionManager")

class PositionManager:
    def __init__(self):
        self.positions = []
        self.capital = Config.VIRTUAL_CAPITAL
        self.notifier = TelegramNotifier()
        self.load_state()
        
        # Ensure CSV exists with headers
        if not os.path.exists(Config.CSV_FILE):
            os.makedirs(os.path.dirname(Config.CSV_FILE), exist_ok=True)
            with open(Config.CSV_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Pair', 'Side', 'Entry Price', 'Trade Size', 'Stop Loss', 'TP1', 'TP2', 'TP3', 'P/L', 'Notes'])

    def load_state(self):
        """Load active positions and capital from JSON."""
        if os.path.exists(Config.PARAMS_FILE):
            try:
                with open(Config.PARAMS_FILE, 'r') as f:
                    data = json.load(f)
                    self.positions = data.get('positions', [])
                    self.capital = data.get('capital', Config.VIRTUAL_CAPITAL)
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                self.positions = []
                self.capital = Config.VIRTUAL_CAPITAL

    def save_state(self):
        """Save active positions and capital to JSON."""
        try:
            with open(Config.PARAMS_FILE, 'w') as f:
                json.dump({
                    'positions': self.positions,
                    'capital': self.capital
                }, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def open_position(self, symbol, trade_params):
        """
        Open a new virtual position.
        """
        if len(self.positions) >= Config.MAX_OPEN_POSITIONS:
            logger.info("Max positions reached. Skipping new trade.")
            return False

        position = {
            'symbol': symbol,
            'entry_time': datetime.now().isoformat(),
            'entry_price': trade_params['entry_price'],
            'size': trade_params['size'],
            'initial_size': trade_params['size'],
            'stop_loss': trade_params['stop_loss'],
            'tp1': trade_params['tp1'],
            'tp2': trade_params['tp2'],
            'tp3': trade_params['tp3'],
            'tp1_hit': False,
            'tp2_hit': False,
            'current_pl': 0.0,
            'notes': 'Open'
        }
        
        self.positions.append(position)
        self.save_state()
        self.log_trade_csv(position, "ENTRY")
        self.notifier.notify_entry(symbol, trade_params)
        logger.info(f"Opened position on {symbol} at {position['entry_price']}")
        return True

    def check_positions(self, current_data):
        """
        Update positions based on current market data.
        current_data is a dict usually: {symbol: {close, high, low}}
        """
        for pos in list(self.positions):
            symbol = pos['symbol']
            if symbol not in current_data:
                continue
                
            price_info = current_data[symbol]
            current_price = price_info['close']  # Or use high/low for strict check?
            # Ideally use High for TP and Low for SL in a candle
            # For simplicity using close if live monitoring, or high/low if candle closed.
            # Assuming 'current_data' comes from live ticker or latest candle
            
            # Use High/Low from latest candle for realistic limits if available, 
            # else use current price.
            high = price_info.get('high', current_price)
            low = price_info.get('low', current_price)
            
            # Check Stop Loss first
            if low <= pos['stop_loss']:
                self.close_position(pos, price=pos['stop_loss'], reason="Stop Loss")
                continue
                
            # Check TP1
            if not pos['tp1_hit'] and high >= pos['tp1']:
                # Sell 33%
                sell_size = pos['initial_size'] * 0.33
                pos['size'] -= sell_size
                pos['tp1_hit'] = True
                
                # Move SL to Break Even
                pos['stop_loss'] = pos['entry_price']
                
                realized_pl = (pos['tp1'] - pos['entry_price']) * sell_size
                self.capital += realized_pl
                
                pos['notes'] = "TP1 Hit"
                self.log_trade_csv(pos, "TP1 Hit", realized_pl)
                self.notifier.notify_tp(symbol, "1", pos['tp1'])
                logger.info(f"{symbol} TP1 Hit. SL moved to BE.")
                self.save_state()
                
            # Check TP2
            if pos['tp1_hit'] and not pos['tp2_hit'] and high >= pos['tp2']:
                # Sell 33% (of original)
                sell_size = pos['initial_size'] * 0.33
                # Create a small buffer if size is getting low (due to floating point)
                if pos['size'] < sell_size: sell_size = pos['size']
                
                pos['size'] -= sell_size
                pos['tp2_hit'] = True
                
                realized_pl = (pos['tp2'] - pos['entry_price']) * sell_size
                self.capital += realized_pl
                
                pos['notes'] = "TP2 Hit"
                self.log_trade_csv(pos, "TP2 Hit", realized_pl)
                self.notifier.notify_tp(symbol, "2", pos['tp2'])
                self.save_state()

            # Check TP3 (Final)
            if pos['tp2_hit'] and high >= pos['tp3']:
                # Sell Remaining (34%)
                sell_size = pos['size']
                
                realized_pl = (pos['tp3'] - pos['entry_price']) * sell_size
                self.capital += realized_pl
                
                self.close_position(pos, price=pos['tp3'], reason="TP3 Full Exit", realized_pl_override=realized_pl, is_partial=False)
                continue

    def close_position(self, pos, price, reason, realized_pl_override=None, is_partial=False):
        """
        Close the position fully (or handle partial close helper logic if needed, but this is mainly for full close).
        """
        if realized_pl_override is None:
            # Calculate P/L for remaining size
            realized_pl = (price - pos['entry_price']) * pos['size']
            self.capital += realized_pl
        else:
            realized_pl = realized_pl_override
            
        pos['notes'] = reason
        self.log_trade_csv(pos, reason, realized_pl)
        
        if reason == "Stop Loss":
            self.notifier.notify_sl(pos['symbol'], price)
        elif "TP3" in reason:
            self.notifier.notify_tp(pos['symbol'], "3", price)
            
        logger.info(f"Closed position {pos['symbol']}: {reason}. P/L: {realized_pl:.2f}")
        
        if pos in self.positions:
            self.positions.remove(pos)
        self.save_state()

    def log_trade_csv(self, pos, status, realized_pl=0.0):
        try:
            with open(Config.CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                # Date, Pair, Side, Entry Price, Trade Size, Stop Loss, TP1, TP2, TP3, P/L, Notes
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    pos['symbol'],
                    "BUY", # Logic assumes Long only
                    pos['entry_price'],
                    f"{pos['size']:.4f}",
                    pos['stop_loss'],
                    pos['tp1'],
                    pos['tp2'],
                    pos['tp3'],
                    f"{realized_pl:.2f}",
                    status
                ])
        except Exception as e:
            logger.error(f"Error writing to CSV: {e}")
