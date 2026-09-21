import math
from skills.market_parser import MarketParser

class PortfolioPerformanceAnalytics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)

    def load_data(self, storage_file: str = None):
        target_storage = storage_file if storage_file else self.storage_file
        try:
            data = self.parser.load_data(target_storage)
        except (OSError, ValueError, TypeError) as e:
            data = []

        if isinstance(data, dict):
            list_data = []
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            i = item.copy()
                            if "symbol" not in i:
                                i["symbol"] = k
                            list_data.append(i)
                        else:
                            list_data.append({"symbol": k, "price": item})
                elif isinstance(v, dict):
                    item = v.copy()
                    if "symbol" not in item:
                        item["symbol"] = k
                    list_data.append(item)
                else:
                    list_data.append({"symbol": k, "price": v})
            return list_data
        elif isinstance(data, list):
            return data
        return []

    def calculate_metrics(self, symbol: str) -> dict:
        data = self.load_data(self.storage_file)
        filtered_prices = []
        for item in data:
            if isinstance(item, dict) and item.get("symbol") == symbol:
                raw_price = item.get("price")
                if raw_price is not None:
                    try:
                        price_val = float(raw_price)
                        filtered_prices.append(price_val)
                    except (ValueError, TypeError):
                        continue

        if not filtered_prices or len(filtered_prices) <= 1:
            return {
                "symbol": symbol,
                "return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0
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

        first_p = filtered_prices[0]
        last_p = filtered_prices[-1]
        total_return = (last_p - first_p) / first_p if first_p != 0 else 0.0

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
            "sharpe_ratio": float(sharpe_ratio)
        }

    def evaluate_performance(self, symbol: str) -> dict:
        return self.calculate_metrics(symbol)

    def __call__(self, symbol: str = None, url: str = None) -> dict:
        if symbol:
            return self.calculate_metrics(symbol)
        return {
            "return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0
        }


def start_new(storage_file: str, symbol: str, url: str) -> dict:
    analytics = PortfolioPerformanceAnalytics(storage_file)
    res = analytics.calculate_metrics(symbol)
    res["symbol"] = symbol
    return res