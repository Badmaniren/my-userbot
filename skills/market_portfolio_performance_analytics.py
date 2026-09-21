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
            # Convert dictionary storage format to list of items expected by metrics calculation
            items = []
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            entry = dict(item)
                            if "symbol" not in entry:
                                entry["symbol"] = k
                            items.append(entry)
                        else:
                            items.append({"symbol": k, "price": item})
                elif isinstance(v, dict):
                    item = dict(v)
                    if "symbol" not in item:
                        item["symbol"] = k
                    items.append(item)
                else:
                    items.append({"symbol": k, "price": v})
            return items
        return data if isinstance(data, list) else []

    def calculate_metrics(self, symbol: str) -> dict:
        data = self.load_data(self.storage_file)

        filtered_prices = [
            item.get("price") for item in data 
            if isinstance(item, dict) and item.get("symbol") == symbol and item.get("price") is not None
        ]
        
        if not filtered_prices or len(filtered_prices) == 1:
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

        total_return = (filtered_prices[-1] - filtered_prices[0]) / filtered_prices[0] if filtered_prices[0] != 0 else 0.0

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

    def generate_ascii_chart(self, symbol: str = None) -> str:
        data = self.load_data(self.storage_file)
        if isinstance(data, list):
            if symbol:
                prices = [
                    item.get("price") for item in data
                    if isinstance(item, dict) and item.get("symbol") == symbol and item.get("price") is not None
                ]
            else:
                prices = [
                    item.get("price") for item in data
                    if isinstance(item, dict) and item.get("price") is not None
                ]
        else:
            prices = []

        if not prices:
            return "[No Data Available]"

        lines = []
        for p in prices:
            try:
                val = float(p)
                bars = "#" * max(1, int(val // 10))
                lines.append(f"{val:.2f}: {bars}")
            except (ValueError, TypeError):
                continue

        return "\n".join(lines) if lines else "[No Data Available]"

    def build_performance_report(self, symbol: str) -> str:
        metrics = self.calculate_metrics(symbol)
        chart = self.generate_ascii_chart(symbol)
        return (
            f"Performance Report for {symbol}:\n"
            f"Return: {metrics['return']:.2%}\n"
            f"Volatility: {metrics['volatility']:.4f}\n"
            f"Sharpe Ratio: {metrics['sharpe_ratio']:.4f}\n\n"
            f"Price Dynamics:\n{chart}"
        )

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
    if url:
        try:
            fetched = analytics.parser.fetch_price(url)
            if isinstance(fetched, (int, float)):
                analytics.parser.fetch_and_store(symbol, float(fetched))
            elif isinstance(fetched, dict) and "price" in fetched:
                analytics.parser.fetch_and_store(symbol, float(fetched["price"]))
        except Exception:
            pass
    return analytics.calculate_metrics(symbol)