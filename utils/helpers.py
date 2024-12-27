from database.db_manager import get_setting

def format_amount(amount, trans_type):
    """Format amount based on transaction type"""
    return amount if trans_type == "Income" else -amount

def format_currency(amount):
    """Format amount as currency using user settings"""
    # Get currency settings
    symbol = get_setting('currency_symbol') or '$'
    position = get_setting('currency_position') or 'before'
    
    # Format the number
    formatted_number = f"{abs(amount):,.2f}"
    
    # Apply currency symbol based on position
    if position == 'before':
        return f"{symbol}{formatted_number}"
    else:
        return f"{formatted_number}{symbol}"