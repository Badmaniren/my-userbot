import json
import os
import skills.db_storage as db_storage
from skills.market_parser import MarketParser

class PortfolioValuation:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def load_data(self, storage_file=None):
        file_to_load = storage_file or self.storage_file
        if hasattr(db_storage, 'load_portfolio'):
            data = db_storage.load_portfolio(file_to_load)
            if data:
                return data
        if hasattr(db_storage, 'load_data'):
            data = db_storage.load_data(file_to_load)
            if data and isinstance(data, dict):
                return data
        if file_to_load and os.path.exists(file_to_load):
            try:
                with open(file_to_load, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    elif isinstance(data, list):
                        res = {}
                        for item in data:
                            if isinstance(item, dict) and "symbol" in item:
                                res[item["symbol"]] = item
                        return res
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                pass
        return {}

    def evaluate_portfolio(self, url):
        portfolio = self.load_data(self.storage_file)
        if not portfolio:
            return {}

        parser = MarketParser(self.storage_file)
        result = {}

        for symbol, data in portfolio.items():
            if not isinstance(data, dict):
                continue

            quantity = float(data.get("quantity", 0.0))
            buy_price = float(data.get("buy_price", 0.0))

            current_price = None
            fetch_error = None

            try:
                fetched = parser.fetch_price(url, symbol)
                if isinstance(fetched, (int, float)) and not isinstance(fetched, bool):
                    current_price = float(fetched)
                elif isinstance(fetched, dict):
                    if symbol in fetched and isinstance(fetched[symbol], (int, float)) and not isinstance(fetched[symbol], bool):
                        current_price = float(fetched[symbol])
                    elif "price" in fetched and isinstance(fetched["price"], (int, float)) and not isinstance(fetched["price"], bool):
                        current_price = float(fetched["price"])
            except Exception as e:
                fetch_error = str(e)

            if current_price is None:
                if "price" in data and isinstance(data["price"], (int, float)) and not isinstance(data["price"], bool):
                    current_price = float(data["price"])
                elif "current_price" in data and isinstance(data["current_price"], (int, float)) and not isinstance(data["current_price"], bool):
                    current_price = float(data["current_price"])

            if current_price is None:
                err_msg = fetch_error if fetch_error else "Could not determine current price"
                result[symbol] = {"error": err_msg}
                continue

            current_value = round(quantity * current_price, 2)
            invested = round(quantity * buy_price, 2)
            pnl = round(current_value - invested, 2)
            pnl_percent = round((pnl / invested) * 100, 2) if invested > 0 else 0.0

            result[symbol] = {
                "current_price": current_price,
                "current_value": current_value,
                "invested": invested,
                "pnl": pnl,
                "pnl_percent": pnl_percent
            }

        return result

    def get_total_summary(self, url):
        evaluated = self.evaluate_portfolio(url)
        total_value = 0.0
        total_invested = 0.0

        for symbol, data in evaluated.items():
            if "error" not in data:
                total_value += data.get("current_value", 0.0)
                total_invested += data.get("invested", 0.0)

        total_pnl = round(total_value - total_invested, 2)

        return {
            "total_value": round(total_value, 2),
            "total_invested": round(total_invested, 2),
            "total_pnl": total_pnl
        }

    def calculate_portfolio_pnl(self, url):
        return self.get_total_summary(url)