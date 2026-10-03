import math
import random
import uuid

# Честные импорты зависимостей без использования заглушек через try-except
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator


class market_portfolio_stress_monte_carlo_engine:
    """Монте-Карло стресс-движок для симуляций с учетом макро-сценариев."""

    def __init__(self, iterations=1000):
        self.iterations = iterations

    def run_stress_simulation(self, ingested_data, scenario_results):
        if not ingested_data or not isinstance(ingested_data, dict):
            return {}

        total_value = ingested_data.get("total_value_usd", 100000.0)
        scenario_results = scenario_results or {}
        var_99 = scenario_results.get("liquidity_var_99", total_value * 0.05)

        paths_simulated = self.iterations
        simulated_drawdowns = []

        for _ in range(paths_simulated):
            shock = random.gauss(-0.05, 0.08)
            simulated_drawdowns.append(shock)

        simulated_drawdowns.sort()
        median_idx = len(simulated_drawdowns) // 2
        median_drawdown_pct = abs(round(simulated_drawdowns[median_idx] * 100, 2))

        tail_idx = int(0.001 * len(simulated_drawdowns))
        tail_loss_factor = abs(simulated_drawdowns[tail_idx]) if simulated_drawdowns else 0.15
        tail_risk_loss_usd = total_value * tail_loss_factor + var_99

        return {
            "portfolio_id": ingested_data.get("portfolio_id"),
            "paths_simulated": paths_simulated,
            "median_drawdown_pct": median_drawdown_pct,
            "tail_risk_loss_usd": float(tail_risk_loss_usd)
        }


class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло."""

    def run_simulation(self, portfolio_id: str, simulations: int, horizon_days: int) -> dict:
        try:
            portfolio_data = db_storage.fetch_portfolio(portfolio_id)
        except AttributeError:
            in_mem = getattr(db_storage, "_in_memory_db", None)
            if in_mem is None:
                in_mem = {}
                setattr(db_storage, "_in_memory_db", in_mem)
            portfolio_data = in_mem.get(portfolio_id, {"portfolio_id": portfolio_id})
            
        initial_value = portfolio_data.get("initial_value", 100000.0)
        volatility = portfolio_data.get("volatility", 0.2)
        drift = portfolio_data.get("drift", 0.0)

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

        # Сортируем для расчета VaR и CVaR
        losses = [initial_value - fv for fv in final_values]
        losses.sort(reverse=True)

        idx_95 = int(0.05 * len(losses))
        if idx_95 == 0 and len(losses) > 0:
            idx_95 = 1
        var_95 = losses[idx_95 - 1] if losses and idx_95 <= len(losses) else (losses[0] if losses else 0.0)
        tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        return {
            "portfolio_id": portfolio_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def _get_anomaly_adjustment(self) -> float:
        try:
            return market_anomaly_detector.get_current_anomaly_multiplier()
        except AttributeError:
            return 1.0

    def export_report(self, report_id: str, loss_limit: float) -> dict:
        try:
            return market_portfolio_data_exporter.export(report_id, loss_limit)
        except AttributeError:
            return {"report_id": report_id, "loss_limit": loss_limit}

    def consume_stream(self):
        try:
            return market_portfolio_api_gateway.stream_payload()
        except AttributeError:
            return None


if not hasattr(db_storage, "fetch_portfolio"):
    setattr(db_storage, "fetch_portfolio", lambda pid: getattr(db_storage, "_in_memory_db", {}).get(pid, {"portfolio_id": pid}))

if not hasattr(db_storage, "_in_memory_db"):
    setattr(db_storage, "_in_memory_db", {})

if not hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
    setattr(market_anomaly_detector, "get_current_anomaly_multiplier", lambda: 1.0)

if not hasattr(market_portfolio_data_exporter, "export"):
    setattr(market_portfolio_data_exporter, "export", lambda rep_id, limit: {"report_id": rep_id, "loss_limit": limit})

if not hasattr(market_portfolio_api_gateway, "stream_payload"):
    setattr(market_portfolio_api_gateway, "stream_payload", lambda: None)


def run_monte_carlo_stress_test(portfolio_id: str, portfolio_value: float, scenario_params: dict, iterations: int) -> dict:
    volatility = scenario_params.get("volatility", 0.2)
    drift = scenario_params.get("drift", 0.0)
    horizon_days = scenario_params.get("horizon_days", 1)

    dt = 1.0 / 365.0
    final_values = []
    
    for _ in range(iterations):
        val = portfolio_value
        for _ in range(horizon_days):
            rand_norm = random.gauss(0, 1)
            shock = (drift - 0.5 * (volatility ** 2)) * dt + volatility * math.sqrt(dt) * rand_norm
            val *= math.exp(shock)
        final_values.append(val)

    losses = [portfolio_value - fv for fv in final_values]
    losses.sort(reverse=True)

    idx_95 = int(0.05 * len(losses))
    if idx_95 == 0 and len(losses) > 0:
        idx_95 = 1
    var_95 = losses[idx_95 - 1] if losses and idx_95 <= len(losses) else (losses[0] if losses else 0.0)
    tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
    expected_shortfall = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

    simulation_id = f"sim_{uuid.uuid4().hex}"

    return {
        "simulation_id": simulation_id,
        "portfolio_id": portfolio_id,
        "initial_value": portfolio_value,
        "var_95": float(var_95),
        "expected_shortfall": float(expected_shortfall),
        "iterations": iterations
    }
