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

        def _extract_price(val):
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return float(val)
            if isinstance(val, dict):
                for key in ("price", "value", "close"):
                    if key in val:
                        v = val.get(key)
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            return float(v)
            return None

        items_to_check = data if isinstance(data, list) else [data]
        for item in items_to_check:
            if not isinstance(item, dict):
                continue

            if item.get("symbol") == symbol:
                p = _extract_price(item)
                if p is not None:
                    filtered_prices.append(p)
            elif symbol in item:
                val = item[symbol]
                if isinstance(val, list):
                    for elem in val:
                        p = _extract_price(elem)
                        if p is not None:
                            filtered_prices.append(p)
                else:
                    p = _extract_price(val)
                    if p is not None:
                        filtered_prices.append(p)

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
            mean_return = 0.0

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