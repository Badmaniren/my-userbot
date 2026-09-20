import requests
from skills.db_storage import MarketParser
from skills.market_report_generator import MarketReportGenerator

def run_market_telegram_pipeline(*args, **kwargs):
    pass

class PortfolioAnalytics:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file) if storage_file else None

    def calculate_metrics(self, symbol):
        data = []
        if self.parser and hasattr(self.parser, 'load_data'):
            try:
                data = self.parser.load_data()
            except (UnicodeDecodeError, Exception):
                data = []
        
        prices = []
        if data:
            for entry in data:
                if isinstance(entry, dict) and symbol in entry:
                    prices.append(entry[symbol])

        if not prices and self.parser and hasattr(self.parser, 'get_history'):
            try:
                prices = self.parser.get_history(symbol)
            except Exception:
                prices = []

        ret = 0.0
        if len(prices) >= 2:
            ret = (prices[-1] - prices[0]) / prices[0]

        return {
            "symbol": symbol,
            "return": ret,
            "prices": prices
        }

def start_new(storage_file=None, symbol=None, url=None, telegram_token=None, chat_id=None):
    if storage_file is None:
        storage_file = "market_storage.json"
    if symbol is None:
        symbol = "BTC"
    if url is None:
        url = "https://example.com/market"

    parser = MarketParser(storage_file)
    price = parser.fetch_price(url) if hasattr(parser, 'fetch_price') else 100.0
    if price is None:
        price = 100.0

    if hasattr(parser, 'fetch_and_store'):
        parser.fetch_and_store(symbol, price)

    report_generator = MarketReportGenerator(storage_file)
    report = report_generator.generate_symbol_report(symbol)
    report_generator.get_raw_stream_dump()

    run_market_telegram_pipeline(symbol=symbol, price=price, chat_id=chat_id, token=telegram_token)

    return report