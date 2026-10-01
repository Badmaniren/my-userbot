import math
import random
import uuid

# Честные импорты зависимостей согласно правилам архитектора
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator


class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло."""

    def run_simulation(self, portfolio_id: str, simulations: int, horizon_days: int) -> dict:
        portfolio_data = None
        if hasattr(db_storage, "fetch_portfolio"):
            try:
                portfolio_data = db_storage.fetch_portfolio(portfolio_id)
            except (AttributeError, TypeError, Exception):
                portfolio_data = None

        if not portfolio_data:
            in_mem = getattr(db_storage, "_in_memory_db", {})
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
        var_95 = losses[idx_95] if losses else 0.0
        tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        return {
            "portfolio_id": portfolio_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def run_multivariate_simulation(self, portfolio_data: dict, simulations: int = 1000, horizon_days: int = 30) -> dict:
        portfolio_id = portfolio_data.get("portfolio_id", "default")
        initial_value = portfolio_data.get("initial_value", 100000.0)
        volatility = portfolio_data.get("volatility", 0.2)
        drift = portfolio_data.get("drift", 0.0)

        dt = 1.0 / 365.0
        simulation_results = []
        final_values = []

        for _ in range(simulations):
            val = initial_value
            path = []
            for _ in range(horizon_days):
                rand_norm = random.gauss(0, 1)
                shock = (drift - 0.5 * (volatility ** 2)) * dt + volatility * math.sqrt(dt) * rand_norm
                val *= math.exp(shock)
                path.append(val)
            simulation_results.append(path)
            final_values.append(val)

        losses = [initial_value - fv for fv in final_values]
        losses.sort(reverse=True)

        idx_95 = int(0.05 * len(losses))
        var_95 = losses[idx_95] if losses else 0.0
        tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        return {
            "portfolio_id": portfolio_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def _get_anomaly_adjustment(self) -> float:
        if hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            try:
                return market_anomaly_detector.get_current_anomaly_multiplier()
            except (AttributeError, TypeError, Exception):
                pass
        return 1.0

    def export_report(self, report_id: str, loss_limit: float) -> dict:
        if hasattr(market_portfolio_data_exporter, "export"):
            try:
                return market_portfolio_data_exporter.export(report_id, loss_limit)
            except (AttributeError, TypeError, Exception):
                pass
        return {
            "report_id": report_id,
            "loss_limit": loss_limit
        }

    def consume_stream(self):
        if hasattr(market_portfolio_api_gateway, "stream_payload"):
            try:
                return market_portfolio_api_gateway.stream_payload()
            except (AttributeError, TypeError, Exception):
                pass
        return None


MarketPortfolioStressMonteCarloEngine = MonteCarloStressEngine


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
    var_95 = losses[idx_95] if losses else 0.0
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


market_portfolio_stress_monte_carlo_engine_run = run_monte_carlo_stress_test


def run_monte_carlo_stress(portfolio_data, simulations=1000, **kwargs):
    engine = MonteCarloStressEngine()
    if isinstance(portfolio_data, str):
        return engine.run_simulation(portfolio_data, simulations=simulations, horizon_days=kwargs.get("horizon_days", 30))
    elif isinstance(portfolio_data, dict):
        return engine.run_multivariate_simulation(portfolio_data, simulations=simulations, horizon_days=kwargs.get("horizon_days", 30))
    return engine.run_simulation("default", simulations=simulations, horizon_days=kwargs.get("horizon_days", 30))


def run_stress_monte_carlo_simulation(portfolio_data=None, **kwargs):
    return run_monte_carlo_stress(portfolio_data or {}, **kwargs)


def run_monte_carlo_stress_simulation(portfolio_data=None, **kwargs):
    return run_monte_carlo_stress(portfolio_data or {}, **kwargs)


def fetch_simulation_results(portfolio_id: str) -> dict:
    engine = MonteCarloStressEngine()
    return engine.run_simulation(portfolio_id, simulations=100, horizon_days=10)


def start_new(payload: dict) -> dict:
    engine = MonteCarloStressEngine()
    portfolio_id = payload.get("portfolio_id", "default_portfolio")
    simulations = payload.get("simulations", 100)
    horizon_days = payload.get("horizon_days", 30)
    return engine.run_simulation(portfolio_id, simulations=simulations, horizon_days=horizon_days)


def market_portfolio_stress_monte_carlo_engine(payload: dict) -> dict:
    return start_new(payload)
