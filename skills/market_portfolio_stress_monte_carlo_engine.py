import uuid
import random
import math

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator


class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло."""

    def __init__(self):
        pass

    def _get_anomaly_adjustment(self) -> float:
        if hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            return float(market_anomaly_detector.get_current_anomaly_multiplier())
        return 1.0

    def run_simulation(self, portfolio_id: str, simulations: int = 100, horizon_days: int = 10) -> dict:
        if not isinstance(portfolio_id, str):
            raise TypeError("portfolio_id must be a string")
        if not isinstance(simulations, int) or simulations <= 0:
            raise ValueError("simulations must be a positive integer")
        if not isinstance(horizon_days, int) or horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")

        portfolio = db_storage.fetch_portfolio(portfolio_id)
        if not portfolio or not isinstance(portfolio, dict):
            portfolio = {
                "portfolio_id": portfolio_id,
                "initial_value": 100000.0,
                "volatility": 0.2,
                "drift": 0.01
            }

        initial_value = float(portfolio.get("initial_value", 100000.0))
        volatility = float(portfolio.get("volatility", 0.2))
        drift = float(portfolio.get("drift", 0.01))

        anomaly_mult = self._get_anomaly_adjustment()
        adjusted_volatility = volatility * anomaly_mult

        simulation_results = []
        final_values = []

        dt = 1.0 / 252.0  # Торговые дни в году

        for _ in range(simulations):
            path = []
            current_val = initial_value
            for _ in range(horizon_days):
                rand_norm = random.gauss(0, 1)
                daily_return = (drift - 0.5 * (adjusted_volatility ** 2)) * dt + adjusted_volatility * math.sqrt(dt) * rand_norm
                current_val *= math.exp(daily_return)
                path.append(current_val)
            simulation_results.append(path)
            final_values.append(current_val)

        # Вычисление VaR и CVaR на горизонте
        sorted_losses = sorted([initial_value - f_val for f_val in final_values])
        index_95 = int(0.95 * len(sorted_losses))
        var_95 = sorted_losses[min(index_95, len(sorted_losses) - 1)]

        tail_losses = sorted_losses[index_95:]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        return {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def run_simulations(self, portfolio_id: str, simulations: int = 100, horizon_days: int = 10) -> dict:
        return self.run_simulation(portfolio_id=portfolio_id, simulations=simulations, horizon_days=horizon_days)

    def run(self, portfolio_id: str, simulations: int = 100, horizon_days: int = 10) -> dict:
        return self.run_simulation(portfolio_id=portfolio_id, simulations=simulations, horizon_days=horizon_days)

    def export_report(self, report_id: str, loss_limit: float) -> dict:
        if hasattr(market_portfolio_data_exporter, "export"):
            return market_portfolio_data_exporter.export(report_id, loss_limit)
        return {}

    def consume_stream(self):
        if hasattr(market_portfolio_api_gateway, "stream_payload"):
            return market_portfolio_api_gateway.stream_payload()
        return None


MarketPortfolioStressMonteCarloEngine = MonteCarloStressEngine


def run_monte_carlo_stress_test(portfolio_id: str, portfolio_value: float, scenario_params: dict, iterations: int = 100) -> dict:
    if not isinstance(portfolio_id, str):
        raise TypeError("portfolio_id must be a string")
    if not isinstance(portfolio_value, (int, float)):
        raise TypeError("portfolio_value must be numeric")
    if not isinstance(scenario_params, dict):
        raise TypeError("scenario_params must be a dict")
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("iterations must be a positive integer")

    portfolio_value = float(portfolio_value)
    volatility = float(scenario_params.get("volatility", 0.2))
    drift = float(scenario_params.get("drift", 0.0))
    horizon_days = int(scenario_params.get("horizon_days", 10))

    dt = 1.0 / 252.0
    final_values = []

    for _ in range(iterations):
        current_val = portfolio_value
        for _ in range(horizon_days):
            rand_norm = random.gauss(0, 1)
            daily_return = (drift - 0.5 * (volatility ** 2)) * dt + volatility * math.sqrt(dt) * rand_norm
            current_val *= math.exp(daily_return)
        final_values.append(current_val)

    sorted_losses = sorted([portfolio_value - f_val for f_val in final_values])
    index_95 = int(0.95 * len(sorted_losses))
    var_95 = sorted_losses[min(index_95, len(sorted_losses) - 1)]

    tail_losses = sorted_losses[index_95:]
    expected_shortfall = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

    simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

    return {
        "simulation_id": simulation_id,
        "portfolio_id": portfolio_id,
        "initial_value": portfolio_value,
        "iterations": iterations,
        "var_95": float(var_95),
        "expected_shortfall": float(expected_shortfall)
    }


def run_monte_carlo_stress(portfolio_data=None, simulations: int = 1000, **kwargs) -> dict:
    engine = MonteCarloStressEngine()
    portfolio_id = portfolio_data.get("portfolio_id", "default_portfolio") if isinstance(portfolio_data, dict) else str(portfolio_data or "default_portfolio")
    return engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations)


def run_stress_monte_carlo_simulation(portfolio_id: str = "default_portfolio", simulations: int = 100, **kwargs) -> dict:
    engine = MonteCarloStressEngine()
    return engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations)


def run_monte_carlo_stress_simulation(portfolio_id: str = "default_portfolio", simulations: int = 100, **kwargs) -> dict:
    engine = MonteCarloStressEngine()
    return engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations)


def start_new(payload: dict = None, **kwargs) -> dict:
    payload = payload or {}
    portfolio_id = payload.get("portfolio_id", "default_portfolio")
    simulations = payload.get("simulations", 100)
    engine = MonteCarloStressEngine()
    return engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations)


def market_portfolio_stress_monte_carlo_engine(payload: dict = None, **kwargs) -> dict:
    return start_new(payload, **kwargs)
