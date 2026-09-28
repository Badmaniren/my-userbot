import os
import json
from typing import List, Dict, Any, Optional, Union

try:
    from skills.db_storage import MarketParser
except ImportError:
    MarketParser = None


class MarketPortfolioMonitor:
    def __init__(
        self,
        storage_file: Optional[str] = None,
        max_allowed_drawdown: float = 0.20,
        db_storage: Any = None
    ):
        self.storage_file = storage_file
        self.max_allowed_drawdown = max_allowed_drawdown
        self.db_storage = db_storage

    def load_data(self, storage_file: Optional[str] = None) -> Dict[str, Any]:
        target_file = storage_file or self.storage_file
        if not target_file or not os.path.exists(target_file):
            return {}
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except Exception:
            return {}

    def save_data(self, data: Dict[str, Any], storage_file: Optional[str] = None) -> bool:
        target_file = storage_file or self.storage_file
        if not target_file:
            return False
        try:
            dirname = os.path.dirname(os.path.abspath(target_file))
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def calculate_drawdown(self, prices: List[float]) -> float:
        if not prices:
            return 0.0
        clean_prices = [float(p) for p in prices if p is not None]
        if not clean_prices:
            return 0.0
        peak = max(clean_prices)
        current = clean_prices[-1]
        if peak <= 0:
            return 0.0
        drawdown = (peak - current) / peak
        return max(0.0, float(drawdown))

    def calculate_peak_to_trough(self, prices: List[float]) -> Dict[str, float]:
        if not prices:
            return {
                "max_drawdown": 0.0,
                "peak": 0.0,
                "trough": 0.0,
                "drawdown_percentage": 0.0
            }
        clean_prices = [float(p) for p in prices if p is not None]
        if not clean_prices:
            return {
                "max_drawdown": 0.0,
                "peak": 0.0,
                "trough": 0.0,
                "drawdown_percentage": 0.0
            }

        peak = clean_prices[0]
        max_drawdown = 0.0
        best_peak = peak
        best_trough = peak

        for price in clean_prices:
            if price > peak:
                peak = price
            if peak > 0:
                dd = (peak - price) / peak
                if dd > max_drawdown:
                    max_drawdown = dd
                    best_peak = peak
                    best_trough = price

        return {
            "max_drawdown": float(max_drawdown),
            "peak": float(best_peak),
            "trough": float(best_trough),
            "drawdown_percentage": float(max_drawdown * 100.0)
        }

    def check_risk_limits(
        self,
        drawdown: float,
        max_allowed: Optional[float] = None
    ) -> Dict[str, Any]:
        limit = max_allowed if max_allowed is not None else self.max_allowed_drawdown
        drawdown_val = float(drawdown) if drawdown is not None else 0.0
        exceeded = drawdown_val > limit
        return {
            "exceeded": exceeded,
            "drawdown": drawdown_val,
            "max_allowed_drawdown": limit,
            "status": "BREACH" if exceeded else "OK"
        }

    def evaluate_portfolio_drawdown(
        self,
        symbol_data_or_series: Union[List[Any], Dict[str, Any]],
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        prices = []
        if isinstance(symbol_data_or_series, list):
            for item in symbol_data_or_series:
                if isinstance(item, (int, float)):
                    prices.append(float(item))
                elif isinstance(item, dict):
                    if "price" in item:
                        prices.append(float(item["price"]))
                    elif "current_price" in item:
                        prices.append(float(item["current_price"]))
        elif isinstance(symbol_data_or_series, dict):
            series = symbol_data_or_series.get("prices") or symbol_data_or_series.get("series") or []
            if isinstance(series, list) and series:
                prices = [float(p) for p in series if isinstance(p, (int, float))]
            elif "price" in symbol_data_or_series or "current_price" in symbol_data_or_series:
                price_val = symbol_data_or_series.get("current_price") or symbol_data_or_series.get("price")
                if price_val is not None:
                    prices = [float(price_val)]

        current_dd = self.calculate_drawdown(prices)
        ptt = self.calculate_peak_to_trough(prices)
        risk = self.check_risk_limits(ptt["max_drawdown"])

        return {
            "symbol": symbol,
            "current_drawdown": current_dd,
            "peak_to_trough": ptt,
            "risk_assessment": risk,
            "data_points": len(prices)
        }

    def run_pipeline(
        self,
        symbol: Optional[str] = None,
        url: Optional[str] = None,
        telegram_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        storage_file: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        target_storage = storage_file or self.storage_file
        data = self.load_data(target_storage)

        # Ensure storage file exists and contains valid JSON if path specified
        if target_storage:
            dirname = os.path.dirname(os.path.abspath(target_storage))
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            if not os.path.exists(target_storage) or os.path.getsize(target_storage) == 0:
                with open(target_storage, "w", encoding="utf-8") as f:
                    json.dump(data if data else {}, f)

        symbol_key = symbol or kwargs.get("ticker", "PORTFOLIO")
        symbol_data = data.get(symbol_key, []) if isinstance(data, dict) else []

        evaluation = self.evaluate_portfolio_drawdown(symbol_data, symbol=symbol_key)

        return {
            "status": "monitored",
            "symbol": symbol_key,
            "url": url,
            "storage_file": target_storage,
            "drawdown": evaluation["current_drawdown"],
            "max_drawdown": evaluation["peak_to_trough"]["max_drawdown"],
            "peak": evaluation["peak_to_trough"]["peak"],
            "trough": evaluation["peak_to_trough"]["trough"],
            "risk_limit_exceeded": evaluation["risk_assessment"]["exceeded"],
            "evaluation": evaluation
        }


def calculate_drawdown(prices: List[float]) -> float:
    return MarketPortfolioMonitor().calculate_drawdown(prices)


def calculate_peak_to_trough(prices: List[float]) -> Dict[str, float]:
    return MarketPortfolioMonitor().calculate_peak_to_trough(prices)


def check_risk_limits(drawdown: float, max_allowed: float = 0.20) -> Dict[str, Any]:
    return MarketPortfolioMonitor(max_allowed_drawdown=max_allowed).check_risk_limits(drawdown, max_allowed)


def run_pipeline(
    symbol: Optional[str] = None,
    url: Optional[str] = None,
    telegram_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    storage_file: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    monitor = MarketPortfolioMonitor(storage_file=storage_file)
    return monitor.run_pipeline(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file,
        **kwargs
    )


def start_new(
    symbol: Optional[str] = None,
    url: Optional[str] = None,
    telegram_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    storage_file: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    return run_pipeline(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file,
        **kwargs
    )


# Aliases
PortfolioMonitor = MarketPortfolioMonitor
market_portfolio_monitor = MarketPortfolioMonitor
