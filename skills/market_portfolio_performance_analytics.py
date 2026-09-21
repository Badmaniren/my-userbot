import math
from skills.market_parser import MarketParser

class PortfolioPerformanceAnalytics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)

    def load_data(self, storage_file: str = None):
        target_storage = storage_file if storage_file else self.storage_file
        data = self.parser.load_data(target_storage)
        if isinstance(data, dict):
            # Convert dictionary storage format to list of items if needed
            list_data = []
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            entry = item.copy()
                            if "symbol" not in entry:
                                entry["symbol"] = k
                            list_data.append(entry)
                        else:
                            list_data.append({"symbol": k, "price": item})
                elif isinstance(v, dict):
                    item = v.copy()
                    if "symbol" not in item:
                        item["symbol"] = k
                    if "history" in item and isinstance(item["history"], list):
                        for hist in item["history"]:
                            if isinstance(hist, dict):
                                h_entry = hist.copy()
                                if "symbol" not in h_entry:
                                    h_entry["symbol"] = k
                                list_data.append(h_entry)
                            else:
                                list_data.append({"symbol": k, "price": hist})
                    else:
                        list_data.append(item)
                else:
                    list_data.append({"symbol": k, "price": v})
            return list_data
        return data

    def calculate_metrics(self, symbol: str) -> dict:
        raw_data = self.load_data(self.storage_file)
        if not isinstance(raw_data, list):
            data = []
        else:
            data = raw_data

        filtered_prices = []
        for item in data:
            if isinstance(item, dict) and item.get("symbol") == symbol and "price" in item:
                p_val = item.get("price")
                if p_val is not None:
                    try:
                        filtered_prices.append(float(p_val))
                    except (ValueError, TypeError):
                        pass
        
        if not filtered_prices:
            return {
                "symbol": symbol,
                "return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0
            }

        if len(filtered_prices) == 1:
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
            if prev != 0 and prev is not None and curr is not None:
                ret = (curr - prev) / prev
                returns.append(ret)
            else:
                returns.append(0.0)

        total_return = (filtered_prices[-1] - filtered_prices[0]) / filtered_prices[0] if filtered_prices[0] and filtered_prices[0] != 0 else 0.0

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
    parser = MarketParser(storage_file)
    parser.fetch_and_store(symbol, url)
    analytics = PortfolioPerformanceAnalytics(storage_file)
    return analytics.calculate_metrics(symbol)