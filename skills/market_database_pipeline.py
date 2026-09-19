from skills.market_parser import MarketParser
from skills.db_storage import MarketDatabaseStorage as DbStorage

class MarketDatabasePipeline:
    def __init__(self, storage_file: str = "market_data.json"):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file=storage_file)
        self.storage = DbStorage(storage_file=storage_file)

    def run_cycle(self, symbol: str, url: str):
        price = self.parser.fetch_price(url)
        self.storage.fetch_and_store(symbol, price)
        return price

    def run_html_parsing_cycle(self, symbol: str, url: str):
        price = self.parser.parse_html_prices(url)
        self.storage.fetch_and_store(symbol, price)
        return price

    def load_market_data(self, filename: str = None):
        target_file = filename if filename is not None else self.storage_file
        return self.storage.load_data(target_file)

    def process_stream(self, stream, symbol: str, price: float):
        self.storage.fetch_and_store(symbol, price)
        return True

    def process_and_store(self, symbol: str, price: float, url: str = None):
        self.storage.fetch_and_store(symbol, price)
        return True