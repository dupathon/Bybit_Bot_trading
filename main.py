import time
import sys
import os
import pandas as pd

# Add project root to sys.path to ensure 'crypto_bot' package is found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto_bot.config import Config
from crypto_bot.utils.logger import setup_logger
from crypto_bot.data.market_data import MarketData
from crypto_bot.strategy.indicators import Indicators
from crypto_bot.strategy.signal_generator import SignalGenerator
from crypto_bot.strategy.trade_manager import TradeManager
from crypto_bot.execution.position_manager import PositionManager

logger = setup_logger("Main")

def main():
    logger.info("Starting Crypto Trading Bot...")
    Config.validate()
    
    # Initialize Components
    market_data = MarketData()
    indicators = Indicators()
    signal_gen = SignalGenerator()
    trade_manager = TradeManager()
    pos_manager = PositionManager()
    
    # Parameters
    SCAN_INTERVAL_SECONDS = 300  # Scan for signals every 5 minutes
    MONITOR_INTERVAL_SECONDS = 180 # Monitor positions every 1 minute
    
    last_scan_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            # 1. Monitor Open Positions
            if pos_manager.positions:
                logger.info(f"Monitoring {len(pos_manager.positions)} active positions...")
                # Fetch current prices for active symbols
                # detailed in position_manager.check_positions
                # We need to construct 'current_data' dict: {symbol: {'close': 1.2, 'high': 1.3, 'low': 1.1}}
                # Using fetch_tickers for efficiency if multiple, or fetch_ticker loop
                active_symbols = [p['symbol'] for p in pos_manager.positions]
                
                # Fetching one by one or batch? ccxt fetch_tickers works for batch usually or all.
                # fetch_tickers(symbols) is supported by binance
                try:
                    tickers = market_data.exchange.fetch_tickers(active_symbols)
                    # Convert to required format
                    current_data = {}
                    for sym, ticker in tickers.items():
                        current_data[sym] = {
                            'close': ticker['last'],
                            'high': ticker['high'], # 24h high? Careful.
                                                    # ticker['high'] is usually 24h high. 
                                                    # For TP/SL within a short interval, we ideally want the "Current Candle High" or just "Current Price".
                                                    # If we use 24h High, we might falsely trigger TP if price WAS high 20 hours ago.
                                                    # SAFETY: Use 'last' price for both High and Low checks to be conservative (checking only current instant).
                                                    # So High = Last, Low = Last. 
                                                    # Unless we fetch OHLCV for the last candle?
                                                    # Fetching OHLCV for monitoring is safer to catch wicks.
                                                    # Let's simply use 'last' price for now (Live Price Monitoring).
                            'low': ticker['last']
                        }
                    
                    pos_manager.check_positions(current_data)
                    
                except Exception as e:
                    logger.error(f"Error fetching tickers for monitoring: {e}")

            # 2. Scan for New Signals (if logic allows)
            if current_time - last_scan_time > SCAN_INTERVAL_SECONDS:
                last_scan_time = current_time
                
                if len(pos_manager.positions) < Config.MAX_OPEN_POSITIONS:
                    logger.info("Scanning for new opportunities...")
                    
                    # 1. Fetch Pairs
                    pairs = market_data.fetch_high_volume_pairs(limit=30) # Limit to top 30 to save API calls
                    
                    candidates = []
                    
                    logger.info(f"Analyzing {len(pairs)} pairs...")
                    
                    for idx, pair in enumerate(pairs, 1):
                        # Skip if already in position
                        if any(p['symbol'] == pair for p in pos_manager.positions):
                            logger.info(f"[{idx}/{len(pairs)}] {pair} - Skipped (already in position)")
                            continue
                        
                        logger.info(f"[{idx}/{len(pairs)}] {pair} - Fetching data...")
                        
                        # Fetch Data
                        df = market_data.fetch_ohlcv(pair, limit=250)
                        if df.empty:
                            logger.info(f"[{idx}/{len(pairs)}] {pair} - ❌ No data available")
                            continue
                        
                        logger.info(f"[{idx}/{len(pairs)}] {pair} - Calculating indicators...")
                        
                        # Indicators
                        df = indicators.add_indicators(df)
                        
                        # Check if indicators were calculated successfully
                        if 'ema_200' not in df.columns or df['ema_200'].isna().all():
                            logger.info(f"[{idx}/{len(pairs)}] {pair} - ❌ Insufficient data for indicators")
                            continue
                        
                        logger.info(f"[{idx}/{len(pairs)}] {pair} - Checking for entry signals...")
                        
                        # Signal
                        signal = signal_gen.check_entry_signal(df)
                        
                        if signal == 'BUY':
                            logger.info(f"[{idx}/{len(pairs)}] {pair} - ✅ BUY SIGNAL FOUND!")
                            candidates.append((pair, df))
                        else:
                            logger.info(f"[{idx}/{len(pairs)}] {pair} - No signal")
                    
                    # Sort candidates or pick top
                    # Since we filtered by volume initially (fetch_high_volume_pairs returns sorted list usually?), 
                    # the candidates are already ordered by volume priority (if fetch_high filters/sorts).
                    # My fetch_high_volume_pairs iterates tickers. Tickers dict is arbitrary order.
                    # I should sort candidates by volume if I want "Liquidity" priority.
                    # But I don't have volume handy in 'candidates' list easily unless I stored it.
                    # Let's just take the first ones found for now.
                    
                    slots_available = Config.MAX_OPEN_POSITIONS - len(pos_manager.positions)
                    
                    for pair, df in candidates[:slots_available]:
                        # Calculate Trade Params
                        # Use last close as entry price or current price?
                        entry_price = df.iloc[-1]['close']
                        
                        params = trade_manager.calculate_trade_params(df, entry_price, pos_manager.capital)
                        
                        if params['size'] > 0:
                            pos_manager.open_position(pair, params)
                else:
                    logger.info("Max positions reached. Skipping scan.")

            # Sleep
            time.sleep(MONITOR_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
