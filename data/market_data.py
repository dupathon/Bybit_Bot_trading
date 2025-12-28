import ccxt
import pandas as pd
import time
from crypto_bot.config import Config
from crypto_bot.utils.logger import setup_logger

logger = setup_logger("MarketData")

class MarketData:
    def __init__(self):
        config_args = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'recvWindow': 60000  # 60 seconds tolerance for timestamp differences
            }
        }
        
        # Only add keys if they look real (not placeholders)
        if Config.BYBIT_API_KEY and not Config.BYBIT_API_KEY.startswith('your_'):
            config_args['apiKey'] = Config.BYBIT_API_KEY
            config_args['secret'] = Config.BYBIT_SECRET_KEY
            
        self.exchange = ccxt.bybit(config_args)
        
    def fetch_high_volume_pairs(self, limit=50):
        """
        Fetch all USDT pairs and filter by volume.
        """
        try:
            markets = self.exchange.load_markets()
            symbols = []
            
            # Get tickers to check volume
            tickers = self.exchange.fetch_tickers()
            
            # Stablecoins to exclude
            stablecoins = ['USDC', 'USDE', 'DAI', 'BUSD', 'TUSD', 'USDT', 'FDUSD', 'USDP', 'GUSD', 'STABLE', 'XAUT']
            
            for symbol, ticker in tickers.items():
                if '/USDT' in symbol:
                    # Extract base currency (e.g., "BTC" from "BTC/USDT")
                    base_currency = symbol.split('/')[0]
                    
                    # Skip if base currency is a stablecoin
                    if base_currency in stablecoins:
                        continue
                    
                    quote_volume = ticker.get('quoteVolume', 0)
                    if quote_volume and quote_volume >= Config.MIN_DAILY_VOLUME_USDT:
                        symbols.append(symbol)
            
            logger.info(f"Found {len(symbols)} pairs with volume >= ${Config.MIN_DAILY_VOLUME_USDT}")
            
            # Save pairs to file
            self._save_pairs_to_file(symbols)
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
            
    def fetch_ohlcv(self, symbol, limit=100):
        """
        Fetch OHLCV data for a symbol.
        """
        try:
            # fetch_ohlcv(symbol, timeframe, since, limit)
            ohlcv = self.exchange.fetch_ohlcv(symbol, Config.TIMEFRAME, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()
    
    def _save_pairs_to_file(self, symbols):
        """
        Save pairs to a file and detect new pairs.
        """
        import os
        from datetime import datetime
        
        pairs_file = 'logs/trading_pairs.txt'
        os.makedirs(os.path.dirname(pairs_file), exist_ok=True)
        
        # Read existing pairs if file exists
        existing_pairs = set()
        if os.path.exists(pairs_file):
            try:
                with open(pairs_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            existing_pairs.add(line.strip())
            except Exception as e:
                logger.error(f"Error reading pairs file: {e}")
        
        # Detect new pairs
        current_pairs = set(symbols)
        new_pairs = current_pairs - existing_pairs
        removed_pairs = existing_pairs - current_pairs
        
        if new_pairs:
            logger.info(f"🆕 New pairs detected: {', '.join(sorted(new_pairs))}")
        
        if removed_pairs:
            logger.info(f"❌ Pairs removed (low volume): {', '.join(sorted(removed_pairs))}")
        
        # Write all current pairs to file
        try:
            with open(pairs_file, 'w') as f:
                f.write(f"# Trading Pairs - Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total Pairs: {len(symbols)}\n")
                f.write(f"# Minimum Volume: ${Config.MIN_DAILY_VOLUME_USDT:,.0f}\n")
                f.write("#\n")
                for symbol in sorted(symbols):
                    f.write(f"{symbol}\n")
            logger.info(f"✅ Pairs list saved to {pairs_file}")
        except Exception as e:
            logger.error(f"Error writing pairs file: {e}")

