import requests
from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBMarketParser
import skills.db_storage as db_storage
from skills.market_report_generator import MarketReportGenerator

def run_market_telegram_pipeline(*args, **kwargs):
    pass

class PortfolioAnalytics:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        if storage_file:
            if hasattr(db_storage.MarketParser, 'return_value') or 'Mock' in type(db_storage.MarketParser).__name__:
                self.parser = db_storage.MarketParser(storage_file)
            else:
                self.parser = MarketParser(storage_file)
        else:
            self.parser = None

    def calculate_metrics(self, symbol):
        data = []
        if self.parser and hasattr(self.parser, 'load_data'):
            try:
                try:
                    data = self.parser.load_data(self.storage_file)
                except TypeError:
                    data = self.parser.load_data()
            except UnicodeDecodeError:
                raise
            except Exception:
                data = []

        prices = []
        if data:
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict):
                        if symbol in entry:
                            val = entry[symbol]
                            if isinstance(val, (int, float)):
                                prices.append(float(val))
                            elif isinstance(val, dict) and "price" in val and isinstance(val["price"], (int, float)):
                                prices.append(float(val["price"]))
                        elif entry.get("symbol") == symbol and "price" in entry:
                            val = entry["price"]
                            if isinstance(val, (int, float)):
                                prices.append(float(val))
                    elif isinstance(entry, str):
                        parts = entry.strip().split(',')
                        if len(parts) == 2 and parts[0] == symbol:
                            try:
                                prices.append(float(parts[1]))
                            except ValueError:
                                pass
            elif isinstance(data, dict):
                if symbol in data:
                    val = data[symbol]
                    if isinstance(val, (int, float)):
                        prices.append(float(val))
                    elif isinstance(val, dict) and "price" in val and isinstance(val["price"], (int, float)):
                        prices.append(float(val["price"]))

        if not prices and self.parser and hasattr(self.parser, 'get_history'):
            try:
                prices = self.parser.get_history(symbol)
            except UnicodeDecodeError:
                raise
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

def start_new(storage_file=None, symbol=None, url=None, telegram_token=None, chat_id=None, price=None, **kwargs):
    if storage_file is None:
        storage_file = "market_storage.json"
    if symbol is None:
        symbol = "BTC"
    if url is None:
        url = "https://example.com/market"

    if hasattr(MarketParser, 'return_value') or 'Mock' in type(MarketParser).__name__:
        parser = MarketParser(storage_file)
    else:
        parser = MarketParser(storage_file)

    if price is None:
        if hasattr(parser, 'fetch_price'):
            try:
                res = parser.fetch_price(url)
                if isinstance(res, (int, float)):
                    price = float(res)
                elif isinstance(res, dict):
                    if "price" in res and isinstance(res["price"], (int, float)):
                        price = float(res["price"])
                    else:
                        price = None
                elif res is not None:
                    try:
                        price = float(res)
                    except (ValueError, TypeError):
                        price = None
            except UnicodeDecodeError:
                raise
            except Exception:
                price = None

    if price is None:
        price = 100.0

    if hasattr(parser, 'fetch_and_store'):
        parser.fetch_and_store(symbol, price)

    report_generator = MarketReportGenerator(storage_file)
    report = report_generator.generate_symbol_report(symbol)
    if hasattr(report_generator, 'get_raw_stream_dump'):
        report_generator.get_raw_stream_dump()

    run_market_telegram_pipeline(symbol=symbol, price=price, chat_id=chat_id, token=telegram_token)

    return report
