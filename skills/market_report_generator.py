from skills.market_parser import MarketParser
from skills import db_storage

class MarketReportGenerator:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)
        self.db = db_storage

    def generate_symbol_report(self, symbol):
        data = self.parser.load_data(self.storage_file)
        
        filtered_data = []
        if isinstance(data, list):
            filtered_data = [item for item in data if isinstance(item, dict) and item.get("symbol") == symbol]
        elif isinstance(data, dict) and symbol in data:
            filtered_data = [{"symbol": symbol, "price": data[symbol]}]
            
        if not filtered_data:
            return {"count": 0, "error": "No data found"}
            
        prices = [item["price"] for item in filtered_data if "price" in item]
        
        if not prices:
            return {"count": 0, "error": "No prices found"}

        return {
            symbol: True,
            'count': len(filtered_data),
            'min_price': min(prices),
            'max_price': max(prices)
        }

    def update_and_fetch_report(self, url, symbol):
        price = self.parser.fetch_price(url)
        self.parser.fetch_and_store(symbol, price)
        return price

    def get_raw_stream_dump(self):
        return self.parser.load_data(self.storage_file)


def generate_market_report(storage_file, symbol):
    load_func = getattr(db_storage, "load_data", None)
    if load_func is None and hasattr(db_storage, "load_db"):
        load_func = db_storage.load_db
    
    data = load_func(storage_file) if load_func else {}
    price = None
    if isinstance(data, dict) and symbol in data:
        price = data[symbol]
    return f"Report for {symbol}: price {price}"