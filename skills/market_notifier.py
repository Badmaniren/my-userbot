from skills.market_parser import MarketParser
from skills.db_storage import DBStorage

class MarketNotifier:
    def __init__(self, parser=None, storage=None, threshold=100.0, storage_file=None):
        self.parser = parser if parser is not None else MarketParser(storage_file=storage_file)
        self.storage = storage if storage is not None else DBStorage()
        self.threshold = threshold

    def check_and_alert(self, symbol, url):
        price = self.parser.fetch_price(url)
        self.parser.fetch_and_store(symbol, price)
        if price >= self.threshold:
            return f"ALERT: {symbol} reached {price}"
        return f"NORMAL: {symbol} at {price}"

    def evaluate_market(self, url):
        prices = self.parser.parse_html_prices(url)
        alerts = []
        for sym, price in prices.items():
            if price >= self.threshold:
                alerts.append((sym, price))
        return alerts

    def check_and_notify(self, symbol, price):
        self.parser.fetch_and_store(symbol, price)
        if price >= self.threshold:
            return True
        return False