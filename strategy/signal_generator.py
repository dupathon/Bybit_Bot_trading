import pandas as pd
from crypto_bot.config import Config

class SignalGenerator:
    def check_entry_signal(self, df):
        """
        Check for Buy Signal:
        1. Price > EMA 200 (Bullish Trend)
        2. EMA 10 Crosses Above EMA 55 (Momentum)
        3. MACD Line > Signal Line (Confirmation)
        """
        if df.empty or len(df) < 200:
            return None
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # 1. Trend Filter: Price > EMA 200
        # Check if Close or High is above EMA 200. Usually Close.
        if current['close'] <= current['ema_200']:
            return None
            
        # 2. Momentum: EMA 10 Crosses EMA 55
        # Current EMA 10 > EMA 55 AND Previous EMA 10 <= Previous EMA 55
        ema_cross = (current['ema_10'] > current['ema_55']) and (previous['ema_10'] <= previous['ema_55'])
        
        if not ema_cross:
            return None
            
        # 3. MACD Confirmation
        # MACD Line > Signal Line
        # Need to dynamically find column names because pandas_ta names them with params
        macd_col = [c for c in df.columns if c.startswith('MACD_') and not c.startswith('MACDs') and not c.startswith('MACDh')][0]
        signal_col = [c for c in df.columns if c.startswith('MACDs_')][0]
        
        if current[macd_col] > current[signal_col]:
            return 'BUY'
            
        return None
