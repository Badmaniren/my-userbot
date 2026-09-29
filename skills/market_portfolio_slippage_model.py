import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


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
        try:
            market_parser = getattr(self, "market_parser", None)
            if market_parser:
                market_parser.parse_market_depth(order_params.ticker)

            if not order_params.ticker or order_params.volume <= 0 or order_params.volatility <= 0:
                raise SlippageCalculationError("Invalid parameters for slippage calculation")

            return round(order_params.volume * order_params.volatility * 0.0001, 6)
        except Exception as e:
            audit_notifier = getattr(self, "audit_notifier", getattr(self, "market_portfolio_audit_alert_notifier", None))
            if audit_notifier:
                audit_notifier.notify_error(str(e))
            if isinstance(e, SlippageCalculationError):
                raise e
            raise SlippageCalculationError(str(e))

    def fetch_external_liquidity_profile(self, ticker: str, volume: float) -> Optional[bytes]:
        api_gateway = getattr(self, "api_gateway", getattr(self, "market_portfolio_api_gateway", None))
        try:
            response = requests.get(f"https://api.example.com/liquidity/{ticker}?volume={volume}")
            if api_gateway:
                api_gateway.log_request(ticker, volume)
            return response.raw
        except Exception:
            if api_gateway:
                api_gateway.log_request(ticker, volume)
            return None

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
        order_id = order_data.get("order_id") or order_data.get("trade_id", "TRD-000")
        symbol = order_data.get("symbol") or order_data.get("ticker", "UNKNOWN")
        side = order_data.get("side", "BUY")
        quantity = order_data.get("quantity") or order_data.get("order_size", 0)
        base_price = order_data.get("price", 100.0)

        adv = market_context.get("adv") or order_data.get("average_daily_volume", 100000)
        volatility = market_context.get("volatility", 0.2)
        spread_bps = market_context.get("spread_bps") or order_data.get("bid_ask_spread_bps", 5.0)

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
            symbol = order.get("symbol") or order.get("ticker", "UNKNOWN")
            context = contexts.get(symbol, {
                "adv": order.get("average_daily_volume", 100000),
                "volatility": 0.2,
                "spread_bps": order.get("bid_ask_spread_bps", 5.0)
            })
            res = self.simulate_order_execution(order, context)
            results.append(res)
        return results

    def evaluate_portfolio_slippage(self, data: Any) -> Dict[str, Any]:
        """Оценивает детали проскальзывания по списку сделок портфеля."""
        if not data:
            return {"status": "ok", "average_slippage_bps": 0.0, "total_evaluations": 0}

        if not isinstance(data, list):
            data = [data]

        model_results = []
        for item in data:
            if not isinstance(item, dict):
                continue
            context = {
                "adv": float(item.get("average_daily_volume", 100000.0)),
                "volatility": float(item.get("volatility", 0.2)),
                "spread_bps": float(item.get("bid_ask_spread_bps", 5.0))
            }
            res = self.simulate_order_execution(item, context)
            model_results.append(res)

        avg_slippage = (
            sum(r["slippage_bps"] for r in model_results) / len(model_results)
            if model_results else 0.0
        )

        return {
            "status": "evaluated",
            "total_evaluations": len(model_results),
            "average_slippage_bps": round(avg_slippage, 2),
            "evaluations": model_results
        }

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
        return []


def market_portfolio_slippage_model(data=None, *args, **kwargs):
    """
    Главная функция-точка входа для расчета проскальзывания портфельных позиций.
    """
    model = MarketPortfolioSlippageModel(**kwargs)
    if data is not None:
        if isinstance(data, (list, dict)):
            return model.evaluate_portfolio_slippage(data)
        if isinstance(data, OrderExecutionParameters):
            return model.calculate_slippage(data)
    return model.evaluate_portfolio_slippage([])


SlippageModel = MarketPortfolioSlippageModel
slippage_model = MarketPortfolioSlippageModel
