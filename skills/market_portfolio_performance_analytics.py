import math
from skills.market_parser import MarketParser


class PortfolioPerformanceAnalytics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)

    def load_data(self, storage_file: str = None):
        target_storage = storage_file if storage_file else self.storage_file
        return self.parser.load_data(target_storage)

    def calculate_metrics(self, symbol: str) -> dict:
        data = self.parser.load_data(self.storage_file)
        filtered_prices = [
            item.get("price")
            for item in data
            if isinstance(item, dict)
            and item.get("symbol") == symbol
            and "price" in item
            and isinstance(item.get("price"), (int, float))
            and not isinstance(item.get("price"), bool)
        ]

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
    parser = MarketParser(storage_file)
    data = parser.load_data(storage_file)

    filtered_prices = [
        item.get("price")
        for item in data
        if isinstance(item, dict)
        and item.get("symbol") == symbol
        and "price" in item
        and isinstance(item.get("price"), (int, float))
        and not isinstance(item.get("price"), bool)
    ]

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