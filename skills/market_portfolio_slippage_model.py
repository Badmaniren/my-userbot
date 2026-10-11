from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    import types
    requests = types.ModuleType("requests")
    class RequestException(Exception): pass
    requests.exceptions = types.SimpleNamespace(RequestException=RequestException)
    requests.get = lambda *args, **kwargs: None


class SlippageCalculationError(Exception):
    """Исключение при ошибке расчета проскальзывания."""
    pass


@dataclass
class OrderExecutionParameters:
    order_id: str
    ticker: str
    volume: float
    volatility: float


class MarketPortfolioSlippageModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.db_storage = kwargs.get("db_storage", None)
        self._execution_logs: Dict[str, List[Dict[str, Any]]] = {}

    def calculate_slippage(self, order_params: OrderExecutionParameters) -> float:
        market_parser = getattr(self, "market_parser", None)
        
        if not order_params.ticker or order_params.volume <= 0 or order_params.volatility <= 0:
            raise SlippageCalculationError("Invalid parameters for slippage calculation")

        depth_factor = 1.0
        if market_parser:
            depth_data = market_parser.parse_market_depth(order_params.ticker)
            if depth_data and isinstance(depth_data, dict):
                available_liquidity = depth_data.get("total_depth", order_params.volume * 10)
                depth_factor = min(2.0, order_params.volume / max(available_liquidity, 1.0))

        return round(order_params.volume * order_params.volatility * 0.0001 * depth_factor, 6)

    def fetch_external_liquidity_profile(self, ticker: str, volume: float) -> Optional[Any]:
        api_gateway = getattr(self, "api_gateway", getattr(self, "market_portfolio_api_gateway", None))
        response = None
        if hasattr(requests, "get"):
            try:
                response = requests.get(f"https://api.example.com/liquidity/{ticker}?volume={volume}")
            except Exception:
                response = None
        if api_gateway:
            api_gateway.log_request(ticker, volume)
        return response.raw if response is not None and hasattr(response, "raw") else None

    def estimate_market_impact(self, order_params: OrderExecutionParameters) -> float:
        anomaly_detector = getattr(self, "anomaly_detector", getattr(self, "market_anomaly_detector", None))
        multiplier = 1.0
        if anomaly_detector:
            anomaly = anomaly_detector.detect(order_params.ticker)
            if anomaly and isinstance(anomaly, dict):
                multiplier = anomaly.get("multiplier", 1.0)
                alert_dispatcher = getattr(self, "alert_dispatcher", getattr(self, "market_portfolio_alert_dispatcher", None))
                if alert_dispatcher:
                    alert_dispatcher.dispatch(anomaly)

        impact = order_params.volume * order_params.volatility * 0.00005 * multiplier
        return float(impact)

    def simulate_stress_slippage(self, ticker: str, volume: float, scenario_name: str) -> Dict[str, Any]:
        stress_scenario_pipeline = getattr(self, "stress_scenario_pipeline", getattr(self, "market_portfolio_stress_scenario_pipeline", None))
        stress_multiplier = 1.0
        if stress_scenario_pipeline:
            sim_result = stress_scenario_pipeline.run_simulation(scenario_name)
            if sim_result and isinstance(sim_result, dict):
                stress_multiplier = sim_result.get("stress_multiplier", 1.0)

        adjusted_slippage = round(volume * 0.2 * 0.0001 * stress_multiplier, 6)
        return {
            "scenario": scenario_name,
            "stress_multiplier": stress_multiplier,
            "adjusted_slippage": adjusted_slippage
        }

    def simulate_order_execution(self, order_data: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        order_id = order_data.get("order_id")
        symbol = order_data.get("symbol")
        side = order_data.get("side", "BUY")
        quantity = order_data.get("quantity", 0)
        base_price = order_data.get("price", 100.0)

        adv = market_context.get("adv", 100000)
        volatility = market_context.get("volatility", 0.2)
        spread_bps = market_context.get("spread_bps", 5.0)

        participation_rate = quantity / adv if adv > 0 else 0.01
        market_impact = base_price * volatility * (participation_rate ** 0.5) * 0.1
        
        half_spread = base_price * (spread_bps / 10000.0)
        
        slippage_value = half_spread + market_impact
        slippage_bps = (slippage_value / base_price) * 10000.0

        if side == "BUY":
            executed_price = base_price + slippage_value
        else:
            executed_price = base_price - slippage_value

        realized_cost = executed_price * quantity

        return {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": base_price,
            "executed_price": round(executed_price, 4),
            "slippage_bps": round(slippage_bps, 2),
            "market_impact": round(market_impact, 4),
            "status": "FILLED",
            "realized_cost": round(realized_cost, 2),
            "effective_slippage": round(slippage_value, 4)
        }

    def simulate_batch(self, orders_batch: List[Dict[str, Any]], contexts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for order in orders_batch:
            symbol = order.get("symbol")
            context = contexts.get(symbol, {"adv": 100000, "volatility": 0.2, "spread_bps": 5.0})
            res = self.simulate_order_execution(order, context)
            results.append(res)
        return results

    def persist_execution_logs(self, simulation_id: str, executions: List[Dict[str, Any]], storage: Any) -> bool:
        self._execution_logs[simulation_id] = executions
        if storage and hasattr(storage, "save_logs"):
            storage.save_logs(simulation_id, executions)
        return True

    def get_execution_logs(self, simulation_id: str, storage: Any) -> List[Dict[str, Any]]:
        if simulation_id in self._execution_logs:
            return self._execution_logs[simulation_id]
        if storage and hasattr(storage, "get_logs"):
            return storage.get_logs(simulation_id)
        if storage and hasattr(storage, "get_log"):
            return storage.get_log(simulation_id)
        return []


def market_portfolio_slippage_model(
    order_size: Optional[float] = None,
    average_daily_volume: Optional[float] = None,
    volatility: Optional[float] = None,
    spread: Optional[float] = None,
    **kwargs
) -> float:
    size = order_size if order_size is not None else kwargs.get("volume", kwargs.get("order_volume", 1000.0))
    adv = average_daily_volume if average_daily_volume is not None else kwargs.get("adv", kwargs.get("average_volume", 100000.0))
    vol = volatility if volatility is not None else kwargs.get("vol", 0.2)
    spr = spread if spread is not None else kwargs.get("spread_bps", 0.0)

    try:
        size = float(size)
    except (ValueError, TypeError):
        size = 1000.0

    try:
        adv = float(adv)
    except (ValueError, TypeError):
        adv = 100000.0

    try:
        vol = float(vol)
    except (ValueError, TypeError):
        vol = 0.2

    try:
        spr = float(spr)
    except (ValueError, TypeError):
        spr = 0.0

    participation_rate = size / adv if adv > 0 else 0.01
    market_impact = vol * (participation_rate ** 0.5)
    half_spread = spr / 2.0 if spr > 0 else 0.0

    slippage = half_spread + market_impact
    return round(float(slippage), 6)


def calculate(volume: float = 1000.0, **kwargs) -> float:
    return market_portfolio_slippage_model(order_size=volume, **kwargs)
