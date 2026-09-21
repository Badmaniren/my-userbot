import math
from skills.market_parser import MarketParser


class PortfolioPerformanceAnalytics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)

    def load_data(self, storage_file: str = None):
        target_storage = storage_file if storage_file else self.storage_file
        data = self.parser.load_data(target_storage)
        if data is None:
            return []
        if isinstance(data, dict):
            return [data]
        if not isinstance(data, list):
            try:
                return list(data)
            except Exception:
                return []
        return data

    def calculate_metrics(self, symbol: str) -> dict:
        data = self.load_data(self.storage_file)
        filtered_prices = []

        def process_item(item):
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                filtered_prices.append(float(item))
            elif isinstance(item, dict):
                if symbol in item:
                    val = item[symbol]
                    if isinstance(val, list):
                        for sub in val:
                            process_item(sub)
                    elif isinstance(val, dict):
                        process_item(val)
                    elif isinstance(val, (int, float)) and not isinstance(val, bool):
                        filtered_prices.append(float(val))
                elif "price" in item and isinstance(item["price"], (int, float)) and not isinstance(item["price"], bool):
                    if "symbol" not in item or item["symbol"] == symbol:
                        filtered_prices.append(float(item["price"]))
                elif "prices" in item and isinstance(item["prices"], list):
                    if "symbol" not in item or item["symbol"] == symbol:
                        for p in item["prices"]:
                            if isinstance(p, (int, float)) and not isinstance(p, bool):
                                filtered_prices.append(float(p))

                for key in ("assets", "holdings"):
                    if key in item and isinstance(item[key], list):
                        for asset in item[key]:
                            if isinstance(asset, dict) and asset.get("symbol") == symbol:
                                process_item(asset)

        if isinstance(data, list):
            for entry in data:
                process_item(entry)
        elif isinstance(data, dict):
            process_item(data)

        if not filtered_prices or len(filtered_prices) == 1:
            return {
                "symbol": symbol,
                "return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
            }

        returns = []
        for i in range(1, len(filtered_prices)):
            prev = filtered_prices[i - 1]
            curr = filtered_prices[i]
            if prev != 0:
                ret = (curr - prev) / prev
                returns.append(ret)
            else:
                returns.append(0.0)

        total_return = (
            (filtered_prices[-1] - filtered_prices[0]) / filtered_prices[0]
            if filtered_prices[0] != 0
            else 0.0
        )

        if returns:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = math.sqrt(variance)
        else:
            volatility = 0.0

        risk_free_rate = 0.0
        if volatility > 0:
            sharpe_ratio = (mean_return - risk_free_rate) / volatility
        else:
            sharpe_ratio = 0.0

        return {
            "symbol": symbol,
            "return": float(total_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
        }

    def evaluate_performance(self, symbol: str) -> dict:
        return self.calculate_metrics(symbol)

    def __call__(self, symbol: str = None, url: str = None) -> dict:
        if symbol:
            return self.calculate_metrics(symbol)
        return {
            "return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
        }


def start_new(storage_file: str, symbol: str, url: str) -> dict:
    analytics = PortfolioPerformanceAnalytics(storage_file)
    return analytics.calculate_metrics(symbol)