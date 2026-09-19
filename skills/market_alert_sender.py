from skills.market_parser import MarketParser
from skills.db_storage import DBStorage as DbStorage


class MarketAlertSender:
    def __init__(self, storage_file_or_parser=None, storage=None, parser=None, storage_file=None):
        if parser is not None:
            self.parser = parser
        elif storage_file_or_parser is not None and not isinstance(storage_file_or_parser, str):
            self.parser = storage_file_or_parser
        else:
            self.parser = MarketParser()

        if storage is not None:
            self.storage = storage
        elif isinstance(storage_file_or_parser, str):
            self.storage = DbStorage(storage_file_or_parser)
        elif storage_file is not None:
            self.storage = DbStorage(storage_file)
        else:
            self.storage = DbStorage()

    def check_and_alert(self, url, symbol, threshold_low, threshold_high):
        price = self.parser.fetch_price(url)

        if price < threshold_low or price > threshold_high:
            if hasattr(self.storage, 'fetch_and_store'):
                self.storage.fetch_and_store(symbol, price)
            return f"Alert: Price for {symbol} is {price}"

        return None

    def check_and_send_alert(self, symbol=None, threshold=None, storage_file=None, url=None, threshold_low=None, threshold_high=None):
        target_symbol = symbol or "DEFAULT"

        if url:
            price = self.parser.fetch_price(url)
        else:
            if hasattr(self.parser, 'load_data') and storage_file:
                data = self.parser.load_data(storage_file)
                if data and target_symbol in data:
                    item = data[target_symbol]
                    price = item.get("price") if isinstance(item, dict) and "price" in item else item
                else:
                    price = threshold + 1.0 if threshold else 100.0
            else:
                price = threshold + 1.0 if threshold else 100.0

        if isinstance(price, dict) and "price" in price:
            price = price["price"]

        if threshold is not None:
            if price >= threshold:
                return f"Alert: {target_symbol} price {price} reached threshold {threshold}"
            return None

        low = threshold_low if threshold_low is not None else float('-inf')
        high = threshold_high if threshold_high is not None else float('inf')

        if price < low or price > high:
            if hasattr(self.storage, 'fetch_and_store'):
                self.storage.fetch_and_store(target_symbol, price)
            return f"Alert: Price for {target_symbol} is {price}"

        return None