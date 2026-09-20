import json
import os
from skills.db_storage import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation


class PortfolioBacktester:
    """Модуль для ретроспективного тестирования портфельных стратегий

    на основе исторических данных из хранилища.
    """

    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def load_historical_data(self, symbol: str) -> list:
        encodings = ["utf-8", "utf-8-sig", "latin-1"]
        data = None
        for enc in encodings:
            try:
                with open(self.storage_file, "r", encoding=enc) as f:
                    data = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            except (FileNotFoundError, OSError):
                return []

        if data is None:
            return []

        # Исправление для юниты: если формат простой ключ-список (в том числе когда symbol совпадает с ключом)
        if isinstance(data, dict):
            if symbol in data:
                res = data[symbol]
                if isinstance(res, list):
                    return res
            for k, v in data.items():
                if k == symbol:
                    if isinstance(v, list):
                        return v
                    elif isinstance(v, dict):
                        for sub_k, sub_v in v.items():
                            if isinstance(sub_v, list):
                                return sub_v
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    if any(item.get("symbol") == symbol or item.get("ticker") == symbol for item in v):
                        return v
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        if sub_k == symbol and isinstance(sub_v, list):
                            return sub_v
            # Если в файле хранится структура MarketParser, где ключи это URL, а внутри лежат данные с нужным символом/тикером
            for k, v in data.items():
                if isinstance(v, list):
                    filtered = [item for item in v if item.get("symbol") == symbol or item.get("ticker") == symbol]
                    if filtered:
                        return filtered
                elif isinstance(v, dict):
                    if v.get("symbol") == symbol or v.get("ticker") == symbol:
                        return [v]
            return []
        elif isinstance(data, list):
            filtered = [item for item in data if item.get("symbol") == symbol or item.get("ticker") == symbol]
            if filtered:
                return filtered
            return data

        return []

    def run_backtest(self, symbol: str, initial_capital: float = 10000.0) -> dict:
        history = self.load_historical_data(symbol)
        if not history or len(history) < 2:
            return {
                "symbol": symbol,
                "final_value": float(initial_capital),
                "total_return": 0.0,
            }

        prices = []
        for item in history:
            if isinstance(item, dict):
                p = item.get("price", item.get("value", item.get("close", 0.0)))
                try:
                    prices.append(float(p))
                except (TypeError, ValueError):
                    pass

        if not prices or len(prices) < 2:
            return {
                "symbol": symbol,
                "final_value": float(initial_capital),
                "total_return": 0.0,
            }

        initial_price = prices[0]
        final_price = prices[-1]

        if initial_price == 0:
            total_return = 0.0
            final_value = float(initial_capital)
        else:
            total_return = ((final_price - initial_price) / initial_price) * 100.0
            final_value = float(initial_capital) * (1.0 + total_return / 100.0)

        return {
            "symbol": symbol,
            "final_value": float(final_value),
            "total_return": float(total_return),
        }

    def calculate_max_drawdown(self, symbol: str) -> float:
        history = self.load_historical_data(symbol)
        if not history:
            return 0.0

        prices = []
        for item in history:
            if isinstance(item, dict):
                p = item.get("price", item.get("value", item.get("close", 0.0)))
                try:
                    prices.append(float(p))
                except (TypeError, ValueError):
                    pass

        if not prices:
            return 0.0

        max_drawdown = 0.0
        peak = prices[0]

        for price in prices:
            if price > peak:
                peak = price
            if peak > 0:
                drawdown = (peak - price) / peak * 100.0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return float(max_drawdown)