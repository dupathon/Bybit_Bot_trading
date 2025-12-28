def calculate_trade_size(capital, risk_percent, entry_price, stop_loss_price):
    """
    Calculate trade size based on risk amount.
    Trade Size = Risk Amount / (Entry - Stop Loss)
    """
    if entry_price <= stop_loss_price:
        return 0.0
    
    risk_amount = capital * risk_percent
    price_diff = entry_price - stop_loss_price
    
    if price_diff == 0:
        return 0.0
        
    size = risk_amount / price_diff
    return size

def format_currency(value):
    return f"${value:.2f}"
