import json
import math
import statistics
from skills.market_parser import MarketParser


def calculate_volatility(prices: list) -> float:
    """Вычисляет стандартное отклонение (волатильность) цен."""
    if not prices or len(prices) < 2:
        return 0.0
    return float(statistics.stdev(prices))


def calculate_max_drawdown(prices: list) -> float:
    """Вычисляет максимальную просадку в процентах (<= 0.0)."""
    if not prices or len(prices) < 2:
        return 0.0

    max_drawdown = 0.0
    peak = prices[0]

    for price in prices:
        if price > peak:
            peak = price
        if peak > 0:
            drawdown = (price - peak) / peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown

    return float(max_drawdown)


def extract_prices(data, symbol: str) -> list:
    """Извлекает список цен для символа из загруженных данных в различных форматах."""
    prices = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                item_symbol = item.get("symbol") or item.get("ticker")
                if item_symbol == symbol and "price" in item:
                    prices.append(float(item["price"]))
    elif isinstance(data, dict):
        if symbol in data:
            entry = data[symbol]
            if isinstance(entry, dict):
                if "history" in entry and isinstance(entry["history"], list):
                    for subitem in entry["history"]:
                        if isinstance(subitem, dict) and "price" in subitem:
                            prices.append(float(subitem["price"]))
                        elif isinstance(subitem, (int, float)):
                            prices.append(float(subitem))
                elif "prices" in entry and isinstance(entry["prices"], list):
                    for p in entry["prices"]:
                        prices.append(float(p))
                elif "price" in entry:
                    prices.append(float(entry["price"]))
            elif isinstance(entry, (int, float)):
                prices.append(float(entry))
            elif isinstance(entry, list):
                for subitem in entry:
                    if isinstance(subitem, dict) and "price" in subitem:
                        prices.append(float(subitem["price"]))
                    elif isinstance(subitem, (int, float)):
                        prices.append(float(subitem))
        else:
            for key, val in data.items():
                if isinstance(val, dict):
                    item_symbol = val.get("symbol") or val.get("ticker") or key
                    if item_symbol == symbol and "price" in val:
                        prices.append(float(val["price"]))
    return prices


class MarketRiskCalculator:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def load_data(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def evaluate_risk(self, symbol: str) -> dict:
        data = self.load_data(self.storage_file)
        prices = extract_prices(data, symbol)

        volatility = calculate_volatility(prices)
        max_drawdown = calculate_max_drawdown(prices)

        return {
            "symbol": symbol,
            "volatility": volatility,
            "max_drawdown": max_drawdown
        }

    def get_risk_summary(self, symbol: str) -> dict:
        data = self.load_data(self.storage_file)
        prices = extract_prices(data, symbol)

        volatility = calculate_volatility(prices)
        max_drawdown = calculate_max_drawdown(prices)

        return {
            "symbol": symbol,
            "volatility": volatility,
            "max_drawdown": max_drawdown,
            "cost_dynamics": prices
        }


def calculate_market_risks(storage_file: str, symbol: str) -> dict:
    calc = MarketRiskCalculator(storage_file)
    return calc.get_risk_summary(symbol)
