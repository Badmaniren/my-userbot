from skills.market_parser import MarketParser
from skills.db_storage import MarketStorage


class MarketNotifier:
    def __init__(self, storage_file: str):
        self.storage_filename = storage_file
        self.parser = MarketParser()
        self.storage = MarketStorage(storage_file)

    def process_and_notify(self, symbol: str, url: str = None, price: float = None) -> bool:
        if price is None:
            if url is None:
                return False
            price = self.parser.fetch_price(url)

        success = self.storage.fetch_and_store(symbol, price)
        return bool(success)

    def get_historical_data(self, filename: str = None):
        target_file = filename or self.storage_filename
        return self.storage.load_data(target_file)