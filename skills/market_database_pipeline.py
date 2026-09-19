from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorage

class MarketDatabasePipeline:
    def __init__(self, storage_file=None):
        self.parser = MarketParser()
        self.storage = DBStorage(storage_file)

    def run_pipeline(self, url=None, symbol=None, price=None):
        if price is not None:
            self.storage.fetch_and_store(symbol, price)
            return True

        fetched_price = self.parser.fetch_price(url)
        self.storage.fetch_and_store(symbol, fetched_price)
        return fetched_price

    def get_stored_data(self, storage_file):
        try:
            return self.storage.load_data(storage_file)
        except UnicodeDecodeError:
            return []

    def process_html_stream(self, url):
        return self.parser.parse_html_prices(url)

    run_cycle = run_pipeline
    run_html_parsing_cycle = process_html_stream
    load_market_data = get_stored_data
    process_stream = process_html_stream
    process_and_store = run_pipeline
