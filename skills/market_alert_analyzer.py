import io
import skills.market_parser as market_parser
import skills.db_storage as db_storage
import skills.market_telegram_pipeline as telegram_pipeline

class MarketAlertAnalyzer:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def check_threshold(self, symbol, url):
        parser = market_parser.MarketParser()
        raw_price = parser.fetch_price(url)

        storage = db_storage.MarketParser(storage_file=self.storage_file)
        data = storage.load_data(self.storage_file) if hasattr(storage, 'load_data') else {}
        if isinstance(data, dict):
            threshold_val = data.get(symbol, 0.0)
            if isinstance(threshold_val, dict):
                threshold = float(threshold_val.get('price', 0.0))
            else:
                threshold = float(threshold_val or 0.0)
        else:
            threshold = 0.0

        if raw_price is None:
            return False

        if isinstance(raw_price, dict):
            price = float(raw_price.get('price', 0.0))
        else:
            price = float(raw_price)

        return price > threshold

    def send_alert(self, token, chat_id, message):
        telegram_pipeline.send_telegram_notification(token, chat_id, message)

    def update_market_data(self, symbol, price):
        storage = db_storage.MarketParser(storage_file=self.storage_file)
        return storage.fetch_and_store(symbol, price)

    def parse_raw_data(self, url):
        parser = market_parser.MarketParser()
        raw_data = parser.parse_html_prices(url)
        if isinstance(raw_data, (bytes, bytearray)):
            io.BytesIO(raw_data)
        return raw_data

    def analyze_thresholds(self, symbol, threshold):
        storage = db_storage.MarketParser(storage_file=self.storage_file)
        stored_data = storage.load_data(self.storage_file) if hasattr(storage, 'load_data') else {}

        alerts = []
        if isinstance(stored_data, dict) and symbol in stored_data:
            symbol_entry = stored_data[symbol]
            if isinstance(symbol_entry, dict):
                current_price = float(symbol_entry.get('price', 0.0))
            else:
                current_price = float(symbol_entry or 0.0)

            if current_price > threshold:
                alerts.append(f"Alert: {symbol} price {current_price} exceeded threshold {threshold}")
        return alerts