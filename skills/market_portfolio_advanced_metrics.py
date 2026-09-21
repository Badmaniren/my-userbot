import os
import json
import math
from skills.market_parser import MarketParser

class PortfolioAdvancedMetrics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.data = self._load_data()

    def _load_data(self) -> dict:
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
        return {}

    def _get_symbol_records(self, symbol: str) -> list:
        if isinstance(self.data, dict):
            symbol_data = self.data.get(symbol, [])
            if isinstance(symbol_data, list):
                return symbol_data
            elif isinstance(symbol_data, (dict, int, float)):
                return [symbol_data]
            return []
        elif isinstance(self.data, list):
            return [item for item in self.data if isinstance(item, dict) and item.get("symbol") == symbol]
        return []

    def calculate_advanced_metrics(self, symbol: str, risk_free_rate: float = 0.02) -> dict:
        records = self._get_symbol_records(symbol)

        prices = []
        for item in records:
            if isinstance(item, dict):
                if "price" in item and isinstance(item["price"], (int, float)):
                    prices.append(float(item["price"]))
            elif isinstance(item, (int, float)):
                prices.append(float(item))

        if len(prices) < 2:
            return {
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown": 0.0,
                "risk_metric": 0.0
            }

        returns = []
        for i in range(1, len(prices)):
            prev = prices[i - 1]
            curr = prices[i]
            if prev != 0:
                returns.append((curr - prev) / prev)
            else:
                returns.append(0.0)

        if not returns:
            return {
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown": 0.0,
                "risk_metric": 0.0
            }

        mean_return = sum(returns) / len(returns)

        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance) * math.sqrt(252) if variance > 0 else 0.0

        negative_returns = [r for r in returns if r < 0]
        downside_variance = sum((r ** 2) for r in negative_returns) / len(returns) if negative_returns else 0.0
        downside_deviation = math.sqrt(downside_variance) * math.sqrt(252) if downside_variance > 0 else 0.0

        annualized_return = mean_return * 252

        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0.0
        sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0.0

        max_drawdown = 0.0
        peak = prices[0]
        for p in prices:
            if p > peak:
                peak = p
            drawdown = (peak - p) / peak if peak > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return {
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "max_drawdown": float(max_drawdown),
            "risk_metric": float(volatility)
        }

    def evaluate_risk_profile(self, symbol: str) -> dict:
        metrics = self.calculate_advanced_metrics(symbol)
        vol = metrics.get("volatility", 0.0)

        if vol < 0.1:
            risk_level = "LOW"
            score = 1.0
        elif vol < 0.3:
            risk_level = "MEDIUM"
            score = 5.0
        else:
            risk_level = "HIGH"
            score = 9.0

        return {
            "risk_level": risk_level,
            "score": float(score)
        }

    def get_metrics_stream_dump(self) -> dict:
        if isinstance(self.data, dict):
            dump = {}
            for sym, val in self.data.items():
                if isinstance(val, list):
                    dump[sym] = val
                elif isinstance(val, (dict, int, float)):
                    dump[sym] = [val]
                else:
                    dump[sym] = []
            return dump
        elif isinstance(self.data, list):
            dump = {}
            for item in self.data:
                if isinstance(item, dict) and "symbol" in item:
                    sym = item["symbol"]
                    dump.setdefault(sym, []).append(item)
            return dump
        return {}