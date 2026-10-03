import skills.db_storage as db_storage
from skills.market_parser import MarketParser

class PortfolioValuation:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def load_data(self, storage_file=None):
        file_to_load = storage_file or self.storage_file
        if hasattr(db_storage, 'load_portfolio'):
            return db_storage.load_portfolio(file_to_load)
        elif hasattr(db_storage, 'load_data'):
            return db_storage.load_data(file_to_load)
        return {}

    def evaluate_portfolio(self, url):
        portfolio = self.load_data(self.storage_file)
        if not portfolio:
            return {}

        parser = MarketParser()
        result = {}

        if isinstance(portfolio, list):
            new_port = {}
            for i, item in enumerate(portfolio):
                if isinstance(item, dict):
                    sym = item.get("symbol", f"item_{i}")
                    new_port[sym] = item
                elif isinstance(item, str):
                    new_port[item] = {"quantity": 1.0, "buy_price": 0.0}
                elif isinstance(item, (int, float)):
                    new_port[f"asset_{i}"] = {"quantity": 1.0, "buy_price": float(item)}
            portfolio = new_port
        elif isinstance(portfolio, (int, float, str)):
            portfolio = {"default": {"quantity": 1.0, "buy_price": float(portfolio) if isinstance(portfolio, (int, float)) else 0.0}}

        if not isinstance(portfolio, dict):
            return {}

        for symbol, data in portfolio.items():
            if isinstance(data, (int, float)):
                data = {"quantity": 1.0, "buy_price": float(data)}
            elif not isinstance(data, dict):
                data = {"quantity": 1.0, "buy_price": 0.0}

            quantity = data.get("quantity", 1.0 if "buy_price" in data else 0.0)
            buy_price = data.get("buy_price", 0.0)

            try:
                current_price = parser.fetch_price(url, symbol)
                if current_price is None:
                    current_price = buy_price
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


class market_portfolio_valuation:
    @staticmethod
    def calculate(portfolio_id):
        v = PortfolioValuation(portfolio_id)
        return v.get_total_summary("http://localhost/api")
