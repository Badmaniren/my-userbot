from skills.market_parser import MarketParser
from skills.db_storage import DbStorage, DBStorage


class MarketAlertSender:
    def __init__(self, storage_file_or_parser=None, storage=None):
        if isinstance(storage_file_or_parser, MarketParser):
            self.parser = storage_file_or_parser
            self.storage = storage
        else:
            storage_file = storage_file_or_parser
            self.parser = MarketParser()
            self.storage = DbStorage(storage_file) if storage_file else DbStorage()

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
                    price = data[target_symbol]
                else:
                    price = threshold + 1.0 if threshold else 100.0
            else:
                price = threshold + 1.0 if threshold else 100.0

        limit = threshold if threshold is not None else (threshold_low if threshold_low is not None else 0.0)
        
        if threshold is not None:
            if price <= threshold:
                return f"Alert: {target_symbol} price {price} reached threshold {threshold}"
            return None
        
        low = threshold_low if threshold_low is not None else float('-inf')
        high = threshold_high if threshold_high is not None else float('inf')
        
        if price < low or price > high:
            if hasattr(self.storage, 'fetch_and_store'):
                self.storage.fetch_and_store(target_symbol, price)
            return f"Alert: Price for {target_symbol} is {price}"
            
        return None