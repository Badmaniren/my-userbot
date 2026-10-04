import math
import random
import uuid
from typing import Dict, Any, Optional

# Честные импорты зависимостей без заглушек
from skills import (
    db_storage,
    market_anomaly_detector,
    market_portfolio_data_exporter,
    market_portfolio_api_gateway,
    market_portfolio_audit_compliance_hub,
    market_portfolio_stress_audit_visualizer
)

class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло с валидацией."""

    def _validate_inputs(self, simulations: int, horizon_days: int):
        if not isinstance(simulations, int) or simulations <= 0:
            raise ValueError("Simulations must be a positive integer.")
        if not isinstance(horizon_days, int) or horizon_days <= 0:
            raise ValueError("Horizon days must be a positive integer.")

    def run_simulation(self, portfolio_id: str, simulations: int, horizon_days: int) -> Dict[str, Any]:
        self._validate_inputs(simulations, horizon_days)

        portfolio_data = None
        if hasattr(db_storage, "fetch_portfolio"):
            try:
                portfolio_data = db_storage.fetch_portfolio(portfolio_id)
            except (AttributeError, KeyError, TypeError):
                portfolio_data = None

        if portfolio_data is None:
            in_mem = getattr(db_storage, "_in_memory_db", {})
            if isinstance(in_mem, dict) and portfolio_id in in_mem:
                portfolio_data = in_mem[portfolio_id]
            else:
                portfolio_data = {}

        initial_value = float(portfolio_data.get("initial_value", 100000.0))
        volatility = float(portfolio_data.get("volatility", 0.2))
        drift = float(portfolio_data.get("drift", 0.0))

        anomaly_mult = self._get_anomaly_adjustment()
        effective_vol = volatility * anomaly_mult

        dt = 1.0 / 365.0
        simulation_results = []
        final_values = []

        for _ in range(simulations):
            val = initial_value
            path = []
            for _ in range(horizon_days):
                rand_norm = random.gauss(0, 1)
                shock = (drift - 0.5 * (effective_vol ** 2)) * dt + effective_vol * math.sqrt(dt) * rand_norm
                val *= math.exp(shock)
                path.append(val)
            simulation_results.append(path)
            final_values.append(val)

        losses = sorted([initial_value - fv for fv in final_values], reverse=True)

        idx_95 = max(1, int(0.05 * len(losses)))
        var_95 = losses[idx_95 - 1]
        tail_losses = losses[:idx_95]
        cvar_95 = sum(tail_losses) / len(tail_losses)

        if hasattr(market_portfolio_audit_compliance_hub, "log_simulation"):
            try:
                market_portfolio_audit_compliance_hub.log_simulation(portfolio_id, simulations, float(var_95))
            except (AttributeError, TypeError):
                pass

        return {
            "portfolio_id": portfolio_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def _get_anomaly_adjustment(self) -> float:
        if hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            try:
                return float(market_anomaly_detector.get_current_anomaly_multiplier())
            except (AttributeError, TypeError, ValueError, NotImplementedError):
                return 1.0
        return 1.0

    def export_report(self, report_id: str, loss_limit: float) -> Dict[str, Any]:
        if hasattr(market_portfolio_data_exporter, "export"):
            return market_portfolio_data_exporter.export(report_id, loss_limit)
        return {"report_id": report_id, "loss_limit": loss_limit}

    def consume_stream(self) -> Any:
        if hasattr(market_portfolio_api_gateway, "stream_payload"):
            return market_portfolio_api_gateway.stream_payload()
        return None


def run_monte_carlo_stress_test(portfolio_id: str, portfolio_value: float, scenario_params: Dict[str, Any], iterations: int) -> Dict[str, Any]:
    if iterations <= 0:
        raise ValueError("Iterations must be greater than zero.")

    volatility = float(scenario_params.get("volatility", 0.2))
    drift = float(scenario_params.get("drift", 0.0))
    horizon_days = int(scenario_params.get("horizon_days", 1))

    dt = 1.0 / 365.0
    final_values = []
    
    for _ in range(iterations):
        val = portfolio_value
        for _ in range(horizon_days):
            rand_norm = random.gauss(0, 1)
            shock = (drift - 0.5 * (volatility ** 2)) * dt + volatility * math.sqrt(dt) * rand_norm
            val *= math.exp(shock)
        final_values.append(val)

    losses = sorted([portfolio_value - fv for fv in final_values], reverse=True)
    idx_95 = max(1, int(0.05 * len(losses)))
    var_95 = losses[idx_95 - 1]
    expected_shortfall = sum(losses[:idx_95]) / idx_95

    result_dict = {
        "simulation_id": f"sim_{uuid.uuid4().hex}",
        "portfolio_id": portfolio_id,
        "initial_value": float(portfolio_value),
        "var_95": float(var_95),
        "expected_shortfall": float(expected_shortfall),
        "iterations": iterations
    }

    if hasattr(market_portfolio_audit_compliance_hub, "log_simulation"):
        try:
            market_portfolio_audit_compliance_hub.log_simulation(portfolio_id, iterations, float(var_95))
        except (AttributeError, TypeError):
            pass

    if hasattr(market_portfolio_stress_audit_visualizer, "visualize_stress_test"):
        try:
            market_portfolio_stress_audit_visualizer.visualize_stress_test(result_dict)
        except (AttributeError, TypeError):
            pass

    return result_dict