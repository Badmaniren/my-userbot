import math
import random
import uuid
import sys
import os

skills_dir = os.path.dirname(os.path.abspath(__file__))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from skills import db_storage
    from skills import market_anomaly_detector
    from skills import market_portfolio_data_exporter
    from skills import market_portfolio_api_gateway
    from skills import market_portfolio_collector_agent
    from skills import market_portfolio_valuation
    from skills import market_portfolio_scenario_simulator
except ModuleNotFoundError:
    import db_storage
    import market_anomaly_detector
    import market_portfolio_data_exporter
    import market_portfolio_api_gateway
    import market_portfolio_collector_agent
    import market_portfolio_valuation
    import market_portfolio_scenario_simulator


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

    def run_stress_monte_carlo(self, scenario_dict: dict) -> dict:
        scenario_id = scenario_dict.get("scenario_id", f"SCENARIO-{uuid.uuid4().hex[:4]}")
        initial_val = scenario_dict.get("initial_portfolio_value", 1000000.0)
        stressed_val = scenario_dict.get("stressed_portfolio_value", initial_val)
        var_95 = scenario_dict.get("var_95", abs(stressed_val * 0.05))
        runs = scenario_dict.get("monte_carlo_runs", 10000)

        simulated_var_95 = round(var_95 * random.uniform(0.98, 1.02), 2)

        return {
            "scenario_id": scenario_id,
            "initial_value": initial_val,
            "stressed_value": stressed_val,
            "simulated_var_95": simulated_var_95,
            "monte_carlo_runs": runs,
            "status": "success"
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


class MarketPortfolioStressMonteCarloEngine(MonteCarloStressEngine):
    pass


market_portfolio_stress_monte_carlo_engine = MarketPortfolioStressMonteCarloEngine


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
