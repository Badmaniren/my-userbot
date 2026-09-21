import requests
from skills import db_storage
from skills.market_parser import MarketParser

def _load_parser_or_db_data(parser, storage_file: str):
    data = {}
    if hasattr(parser, "load_data"):
        try:
            data = parser.load_data(storage_file)
        except TypeError:
            try:
                data = parser.load_data()
            except TypeError:
                data = {}

    if not data:
        if hasattr(db_storage, "load_data"):
            data = db_storage.load_data(storage_file)
        elif hasattr(db_storage, "get_data"):
            data = db_storage.get_data(storage_file)

    return data

def send_telegram_notification(token: str, chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response

def run_pipeline(symbol: str, url: str, telegram_token: str, chat_id: str, storage_file: str):
    parser = MarketParser(storage_file)
    price = parser.fetch_price(url)
    parser.fetch_and_store(symbol, price)
    
    data = _load_parser_or_db_data(parser, storage_file)
        
    current_price = data.get(symbol, price) if isinstance(data, dict) else price
    
    message = f"Market Update: {symbol} = {current_price}"
    resp = send_telegram_notification(telegram_token, chat_id, message)
    if resp.status_code == 200:
        return True
    return False

def run_market_telegram_pipeline(storage_file: str, symbol: str, chat_id: str, url: str = "https://example.com", telegram_token: str = "123456:ABC-DEF1234abcdWxyz-1234567890"):
    parser = MarketParser(storage_file)
    
    data = _load_parser_or_db_data(parser, storage_file)
        
    price = data.get(symbol, 0.0) if isinstance(data, dict) else 0.0
    
    message = f"Integration Market Update: {symbol} = {price}"
    send_telegram_notification(telegram_token, chat_id, message)
    
    return {
        "status": "success",
        "sent_symbol": symbol,
        "sent_price": price
    }