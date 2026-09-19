import requests
from skills import market_parser
from skills import db_storage

def check_and_alert(symbol, url, threshold, chat_id="DEFAULT_CHAT", token="DEFAULT_TOKEN"):
    price = market_parser.fetch_price(url)
    db_storage.fetch_and_store(symbol, price)
    
    if price >= threshold:
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"Alert! Symbol {symbol} reached price {price} (Threshold: {threshold})"
        }
        response = requests.post(api_url, json=payload)
        return True
    return False

def process_stream_alert(stream, token="DEFAULT_TOKEN"):
    data = stream.read()
    parsed = market_parser.parse_html_prices(data)
    return parsed

class TelegramAlertService:
    def __init__(self, db_storage=None, market_parser=None):
        self.db = db_storage
        self.parser = market_parser

    def check_and_alert(self, symbol, threshold, chat_id="DEFAULT_CHAT", token="DEFAULT_TOKEN", url="https://example.com"):
        if self.parser and hasattr(self.parser, 'fetch_price'):
            try:
                price = self.parser.fetch_price(url)
            except AttributeError:
                price = market_parser.fetch_price(url)
        else:
            price = market_parser.fetch_price(url)
            
        if self.db and hasattr(self.db, 'fetch_and_store'):
            self.db.fetch_and_store(symbol, price)
        else:
            db_storage.fetch_and_store(symbol, price)
            
        if price >= threshold:
            api_url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": f"Alert! Symbol {symbol} reached price {price} (Threshold: {threshold})"
            }
            requests.post(api_url, json=payload)
            return True
        return False