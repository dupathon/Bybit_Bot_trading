import pandas as pd
import pandas_ta as ta
from crypto_bot.config import Config

class Indicators:
    @staticmethod
    def add_indicators(df):
        """
        Add EMA 200, 55, 10, MACD, ATR to the dataframe.
        """
        if df.empty:
            return df
            
        # EMAs
        # EMAs
        # EMAs
        # EMAs
        # Calculate separately and assign to avoid ambiguity and ensure naming
        ema_200 = df.ta.ema(length=Config.EMA_LONG)
        if isinstance(ema_200, pd.DataFrame): ema_200 = None  # Invalid result
        
        ema_55 = df.ta.ema(length=Config.EMA_MEDIUM)
        if isinstance(ema_55, pd.DataFrame): ema_55 = None
        
        ema_10 = df.ta.ema(length=Config.EMA_SHORT)
        if isinstance(ema_10, pd.DataFrame): ema_10 = None
        
        # Assign explicitly
        if ema_200 is not None: df['ema_200'] = ema_200
        if ema_55 is not None: df['ema_55'] = ema_55
        if ema_10 is not None: df['ema_10'] = ema_10
        
        # MACD
        # pandas_ta macd returns columns likes MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        # separating them for clarity
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        if macd is not None:
             df = pd.concat([df, macd], axis=1)
             # Rename for easier access if needed, but standard names are fine.
             # MACD_12_26_9 is the MACD line
             # MACDs_12_26_9 is the Signal line
             # MACDh_12_26_9 is the Histogram
        
        # ATR
        df['atr'] = df.ta.atr(length=Config.ATR_PERIOD)
        
        return df
