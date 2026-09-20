import json
import os
from skills.market_parser import MarketParser
from skills import db_storage

class MarketStatusAnalyzer:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)

        # Check if db_storage contains a class or callable named db_storage/DBStorage/etc., else use db_storage module/object
        storage_cls = getattr(db_storage, 'db_storage', None) or getattr(db_storage, 'DBStorage', None) or getattr(db_storage, 'MarketStorage', None)
        if storage_cls and callable(storage_cls):
            try:
                self.storage = storage_cls(storage_file)
            except Exception:
                self.storage = db_storage
        else:
            self.storage = db_storage

    def compute_base_metrics(self, prices: list) -> dict:
        if not prices:
            return {"min": 0.0, "max": 0.0, "average": 0.0}
        numeric_prices = [p for p in prices if isinstance(p, (int, float))]
        if not numeric_prices:
            return {"min": 0.0, "max": 0.0, "average": 0.0}
        return {
            "min": min(numeric_prices),
            "max": max(numeric_prices),
            "average": sum(numeric_prices) / len(numeric_prices)
        }

    def _extract_history(self) -> list:
        history = []
        if hasattr(self.storage, 'load_data'):
            try:
                history = self.storage.load_data(self.storage_file)
            except TypeError:
                history = self.storage.load_data()
        elif hasattr(self.storage, 'get_data'):
            try:
                history = self.storage.get_data(self.storage_file)
            except TypeError:
                history = self.storage.get_data()
        elif hasattr(self.parser, 'load_data'):
            try:
                history = self.parser.load_data(self.storage_file)
            except TypeError:
                history = self.parser.load_data()

        if isinstance(history, dict):
            converted = []
            for k, v in history.items():
                if isinstance(v, (int, float)):
                    converted.append({"symbol": k, "price": float(v)})
                elif isinstance(v, dict):
                    item = {"symbol": k}
                    item.update(v)
                    converted.append(item)
            history = converted
        elif isinstance(history, list):
            parsed_list = []
            for item in history:
                if isinstance(item, dict):
                    parsed_list.append(item)
                elif isinstance(item, str):
                    s = item.strip()
                    if "," in s:
                        parts = s.split(",")
                        if len(parts) >= 2:
                            try:
                                parsed_list.append({"symbol": parts[0].strip(), "price": float(parts[1].strip())})
                            except ValueError:
                                pass
                    else:
                        try:
                            parsed_list.append(json.loads(s))
                        except Exception:
                            pass
            history = parsed_list

        if not history and os.path.exists(self.storage_file):
            if self.storage_file.endswith('.json'):
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            history = data
                        elif isinstance(data, dict):
                            history = [{"symbol": k, "price": float(v)} for k, v in data.items() if isinstance(v, (int, float))]
                except Exception:
                    pass

        return history if isinstance(history, list) else []

    def analyze_market_status(self, *args, **kwargs):
        if len(args) == 1:
            symbol = args[0]
            url = kwargs.get('url', f"https://example.com/market/{symbol.lower()}")
        elif len(args) >= 2:
            url, symbol = args[0], args[1]
        else:
            url = kwargs.get('url', '')
            symbol = kwargs.get('symbol', '')

        current_price = self.parser.fetch_price(url)
        if isinstance(current_price, dict):
            current_price = current_price.get('price')

        history = self._extract_history()

        symbol_prices = [item.get("price") for item in history if isinstance(item, dict) and item.get("symbol") == symbol and item.get("price") is not None]

        if not symbol_prices and history:
            symbol_prices = [item.get("price") for item in history if isinstance(item, dict) and item.get("price") is not None]

        if not symbol_prices and isinstance(current_price, (int, float)):
            symbol_prices = [current_price]

        metrics = self.compute_base_metrics(symbol_prices)

        trend = "neutral"
        if len(symbol_prices) >= 2 and isinstance(symbol_prices[-1], (int, float)) and isinstance(symbol_prices[-2], (int, float)):
            if symbol_prices[-1] > symbol_prices[-2]:
                trend = "bullish"
            elif symbol_prices[-1] < symbol_prices[-2]:
                trend = "bearish"
        elif isinstance(current_price, (int, float)) and metrics["average"] > 0:
            if current_price > metrics["average"]:
                trend = "bullish"
            elif current_price < metrics["average"]:
                trend = "bearish"

        result = {
            "symbol": symbol,
            "current_price": current_price,
            "trend": trend,
        }
        result.update(metrics)
        return result

    def fetch_and_evaluate_stream(self, url: str):
        if hasattr(self.parser, 'parse_html_prices'):
            return self.parser.parse_html_prices(url)
        return None
