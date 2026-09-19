import requests
from skills import market_parser
from skills import db_storage

def _extract_price(price_data):
    if isinstance(price_data, dict):
        if "price" in price_data:
            try:
                return float(price_data["price"])
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    elif isinstance(price_data, (int, float)):
        return float(price_data)
    elif isinstance(price_data, str):
        try:
            return float(price_data)
        except ValueError:
            return 0.0
    return 0.0

def check_and_alert(symbol, url, threshold, chat_id="DEFAULT_CHAT", token="DEFAULT_TOKEN"):
    raw_price = market_parser.fetch_price(url)
    price = _extract_price(raw_price)

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
            raw_price = self.parser.fetch_price(url)
        else:
            raw_price = market_parser.fetch_price(url)

        price = _extract_price(raw_price)

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
