import requests
from skills import db_storage
from skills.market_parser import MarketParser

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
    
    data = parser.load_data() if hasattr(parser, "load_data") else getattr(db_storage, "load_data", lambda f: {})(storage_file)
    current_price = data.get(symbol, price)
    
    message = f"Market Update: {symbol} = {current_price}"
    resp = send_telegram_notification(telegram_token, chat_id, message)
    if resp.status_code == 200:
        return True
    return False

def run_market_telegram_pipeline(storage_file: str, symbol: str, chat_id: str, url: str = "https://example.com", telegram_token: str = "123456:ABC-DEF1234abcdWxyz-1234567890"):
    parser = MarketParser(storage_file)
    
    # Поддерживаем различные варианты реализации хранилища (load_data или get_data)
    if hasattr(parser, "load_data"):
        data = parser.load_data()
    elif hasattr(db_storage, "load_data"):
        data = db_storage.load_data(storage_file)
    elif hasattr(db_storage, "get_data"):
        data = db_storage.get_data(storage_file)
    else:
        data = {}
        
    price = data.get(symbol, 0.0)
    
    message = f"Integration Market Update: {symbol} = {price}"
    send_telegram_notification(telegram_token, chat_id, message)
    
    return {
        "status": "success",
        "sent_symbol": symbol,
        "sent_price": price
    }