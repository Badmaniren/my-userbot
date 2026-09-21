import math
import logging
from skills.market_parser import MarketParser

logger = logging.getLogger(__name__)

class PortfolioPerformanceAnalytics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)
        logger.debug(f"Initialized PortfolioPerformanceAnalytics with storage: {storage_file}")

    def load_data(self, storage_file: str = None):
        target_storage = storage_file if storage_file else self.storage_file
        logger.debug(f"Loading data from storage: {target_storage}")
        try:
            raw_data = self.parser.load_data(target_storage)
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error loading storage file {target_storage}: {e}")
            return []

        if isinstance(raw_data, dict):
            formatted_data = []
            for sym, details in raw_data.items():
                if isinstance(details, dict):
                    item = {"symbol": sym}
                    item.update(details)
                    formatted_data.append(item)
                else:
                    formatted_data.append({"symbol": sym, "price": details})
            return formatted_data
        elif isinstance(raw_data, list):
            return raw_data
        return []

    def calculate_metrics(self, symbol: str) -> dict:
        logger.info(f"Calculating metrics for symbol: {symbol}")
        data = self.load_data(self.storage_file)
        
        filtered_prices = []
        for item in data:
            if isinstance(item, dict) and item.get("symbol") == symbol:
                if "history" in item and isinstance(item["history"], list) and len(item["history"]) > 0:
                    for hist in item["history"]:
                        if isinstance(hist, dict) and hist.get("price") is not None:
                            filtered_prices.append(hist.get("price"))
                        elif isinstance(hist, (int, float)):
                            filtered_prices.append(hist)
                elif "price" in item and item.get("price") is not None:
                    filtered_prices.append(item.get("price"))

        if not filtered_prices:
            filtered_prices = [
                item.get("price") for item in data
                if isinstance(item, dict) and item.get("symbol") == symbol and item.get("price") is not None
            ]

        if not filtered_prices or len(filtered_prices) < 2:
            logger.debug(f"Insufficient price data for symbol {symbol}. Returning zero metrics.")
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
            if prev is not None and curr is not None and prev != 0:
                ret = (curr - prev) / prev
                returns.append(ret)
            else:
                returns.append(0.0)

        total_return = (filtered_prices[-1] - filtered_prices[0]) / filtered_prices[0] if filtered_prices[0] is not None and filtered_prices[0] != 0 else 0.0

        if returns:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = math.sqrt(variance)
        else:
            mean_return = 0.0
            volatility = 0.0

        risk_free_rate = 0.0
        if volatility > 0:
            sharpe_ratio = (mean_return - risk_free_rate) / volatility
        else:
            sharpe_ratio = 0.0

        logger.debug(f"Successfully calculated metrics for {symbol}: return={total_return}, volatility={volatility}, sharpe={sharpe_ratio}")
        return {
            "symbol": symbol,
            "return": float(total_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio)
        }

    def evaluate_performance(self, symbol: str) -> dict:
        logger.debug(f"Evaluating performance for symbol: {symbol}")
        return self.calculate_metrics(symbol)

    def __call__(self, symbol: str = None, url: str = None) -> dict:
        if symbol:
            logger.debug(f"Calling PortfolioPerformanceAnalytics with symbol: {symbol}")
            return self.calculate_metrics(symbol)
        logger.debug("Calling PortfolioPerformanceAnalytics without symbol. Returning default empty metrics.")
        return {
            "return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0
        }


def start_new(storage_file: str, symbol: str, url: str) -> dict:
    logger.info(f"Starting new performance analysis for symbol: {symbol} with storage: {storage_file}")
    analytics = PortfolioPerformanceAnalytics(storage_file)
    return analytics.calculate_metrics(symbol)
