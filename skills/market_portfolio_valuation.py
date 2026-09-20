import json
import os
import skills.db_storage as db_storage
from skills.market_parser import MarketParser

class PortfolioValuation:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def load_data(self, storage_file=None):
        file_to_load = storage_file or self.storage_file
        if not file_to_load:
            return {}
        if isinstance(file_to_load, str) and os.path.exists(file_to_load):
            try:
                with open(file_to_load, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        if hasattr(db_storage, 'load_portfolio'):
            return db_storage.load_portfolio(file_to_load)
        elif hasattr(db_storage, 'load_data'):
            res = db_storage.load_data(file_to_load)
            if res and not (isinstance(res, list) and res and isinstance(res[0], str)):
                return res
        return {}

    def evaluate_portfolio(self, url):
        portfolio = self.load_data(self.storage_file)
        if not portfolio:
            return {}

        parser = MarketParser()
        result = {}

        items = []
        if isinstance(portfolio, dict):
            for k, v in portfolio.items():
                if isinstance(v, dict):
                    items.append((k, v.get("quantity", 1.0), v.get("buy_price", v.get("price", 0.0))))
                elif isinstance(v, (int, float)):
                    items.append((k, 1.0, float(v)))
        elif isinstance(portfolio, list):
            for entry in portfolio:
                if isinstance(entry, dict):
                    sym = entry.get("symbol")
                    if sym:
                        items.append((
                            sym,
                            entry.get("quantity", 1.0),
                            entry.get("buy_price", entry.get("price", 0.0))
                        ))

        for symbol, quantity, buy_price in items:
            current_price = buy_price
            if url:
                try:
                    fetched = parser.fetch_price(url)
                    if isinstance(fetched, (int, float)):
                        current_price = float(fetched)
                    elif isinstance(fetched, dict) and "price" in fetched and isinstance(fetched["price"], (int, float)):
                        current_price = float(fetched["price"])
                except Exception as e:
                    result[symbol] = {"error": str(e)}
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