import os
import json
import logging
from skills import market_parser
from skills import db_storage

logger = logging.getLogger(__name__)

class MarketNotifier:
    def __init__(self, storage_file="market_storage.json"):
        self.storage_file = storage_file
        self.parser = market_parser.MarketParser() if hasattr(market_parser, "MarketParser") else market_parser
        self.storage = db_storage

    def _parse_data(self, data):
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            res = {}
            for item in data:
                if isinstance(item, str) and ',' in item:
                    parts = item.strip().split(',')
                    if len(parts) >= 2:
                        try:
                            res[parts[0]] = float(parts[1])
                        except ValueError:
                            pass
                elif isinstance(item, tuple) and len(item) >= 2:
                    try:
                        res[item[0]] = float(item[1])
                    except ValueError:
                        pass
                elif isinstance(item, dict) and 'symbol' in item and 'price' in item:
                    try:
                        res[item['symbol']] = float(item['price'])
                    except (ValueError, TypeError):
                        pass
            return res
        return {}

    def _load_from_file(self):
        if not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
                return self._parse_data(data)
        except Exception as e:
            logger.warning(f"Failed to load market storage file '{self.storage_file}': {e}")
            return {}

    def _save_to_file(self, data):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save market storage file '{self.storage_file}': {e}")

    def check_and_notify(self, symbol, url, threshold):
        price = self.parser.fetch_price(url)
        alert_triggered = price > threshold

        if hasattr(self.storage, "fetch_and_store"):
            self.storage.fetch_and_store(symbol, price)
        elif hasattr(self.storage, "save_market_data"):
            data = self.load_history()
            data[symbol] = price
            self.storage.save_market_data(self.storage_file, data)
        elif hasattr(self.storage, "save_data"):
            data = self.load_history()
            data[symbol] = price
            self.storage.save_data(self.storage_file, data)
        else:
            data = self.load_history()
            data[symbol] = price
            self._save_to_file(data)

        return {
            "symbol": symbol,
            "price": price,
            "alert_triggered": alert_triggered
        }

    def load_history(self):
        if hasattr(self.storage, "load_market_data"):
            data = self.storage.load_market_data(self.storage_file)
            if data is not None:
                return self._parse_data(data)
        if hasattr(self.storage, "load_data"):
            data = self.storage.load_data(self.storage_file)
            if data is not None:
                return self._parse_data(data)
        return self._load_from_file()

    def send_alert(self, symbol, price, threshold):
        return f"ALERT: {symbol} reached price {price} (Threshold: {threshold})"

    def process_and_notify(self, symbol, url, target_price):
        price = self.parser.fetch_price(url)
        alert_triggered = price >= target_price

        data = self.load_history()
        data[symbol] = price

        if hasattr(self.storage, "save_market_data"):
            self.storage.save_market_data(self.storage_file, data)
        elif hasattr(self.storage, "save_data"):
            self.storage.save_data(self.storage_file, data)
        elif hasattr(self.storage, "fetch_and_store"):
            self.storage.fetch_and_store(symbol, price)
        else:
            self._save_to_file(data)

        return {
            "symbol": symbol,
            "price": price,
            "alert_triggered": alert_triggered
        }
