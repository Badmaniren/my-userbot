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
            items = [(f"asset_{i}", item) for i, item in enumerate(portfolio)]
        elif isinstance(portfolio, dict):
            items = portfolio.items()
        else:
            items = [("asset_0", portfolio)]

        for symbol, data in items:
            if isinstance(data, dict):
                quantity = float(data.get("quantity", 0.0))
                buy_price = float(data.get("buy_price", 0.0))
            elif isinstance(data, (int, float)):
                quantity = 1.0
                buy_price = float(data)
            elif isinstance(data, list):
                quantity = float(len(data))
                buy_price = 0.0
            else:
                quantity = 0.0
                buy_price = 0.0

            try:
                current_price = parser.fetch_price(url, symbol)
                if isinstance(current_price, dict):
                    current_price = float(current_price.get("price", 0.0))
                elif not isinstance(current_price, (int, float)):
                    current_price = 0.0
                else:
                    current_price = float(current_price)
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
            if isinstance(data, dict) and "error" not in data:
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
