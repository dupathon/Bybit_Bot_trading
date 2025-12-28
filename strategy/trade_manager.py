from crypto_bot.config import Config
from crypto_bot.utils.helpers import calculate_trade_size

class TradeManager:
    def calculate_trade_params(self, df, entry_price, capital):
        """
        Calculate Stop Loss, TPs, and Position Size.
        Returns a dict of trade parameters.
        """
        current_atr = df.iloc[-1]['atr']
        
        # SL = Entry - (ATR * 2)
        stop_loss = entry_price - (current_atr * Config.ATR_MULTIPLIER)
        
        # Risk Calculation
        trade_size = calculate_trade_size(capital, Config.RISK_PER_TRADE_PERCENT, entry_price, stop_loss)
        
        # Take Profits (Risk:Reward based or Fixed? User said: "TP1 -> 33% of position")
        # Usually TP levels are distance based or RR based. User didn't specify RR, 
        # but often it's 1:1, 1:1.5, 1:2. 
        # Or based on ATR? 
        # User only said "TP1 -> 33%". Let's assume some reasonable levels or ask.
        # Given "Trend Following", often we let it run.
        # Let's use ATR based TPs for now:
        # TP1 = Entry + 1*ATR
        # TP2 = Entry + 2*ATR
        # TP3 = Entry + 3*ATR
        # Or just standard risk multiples 1R, 2R, 3R.
        # Since SL is 2*ATR, 1R would be 2*ATR distance.
        # Let's set TP1 = 1R (2*ATR), TP2 = 1.5R, TP3 = 2R.
        
        risk_distance = entry_price - stop_loss
        
        tp1 = entry_price + risk_distance      # 1:1 Risk Reward
        tp2 = entry_price + (risk_distance * 1.5)
        tp3 = entry_price + (risk_distance * 2.0) # Or just let it ride? User has fixed 3 TPs.
        
        return {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'size': trade_size,
            'atr': current_atr
        }
