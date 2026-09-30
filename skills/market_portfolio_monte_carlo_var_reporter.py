import uuid
import sys
import types

if "requests" not in sys.modules:
    try:
        import requests
    except ImportError:
        requests = types.ModuleType("requests")
        def _post(*args, **kwargs):
            raise NotImplementedError("requests module is not installed")
        requests.post = _post
        requests.get = lambda *args, **kwargs: None
        sys.modules["requests"] = requests
else:
    requests = sys.modules["requests"]

from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from skills.db_storage import db_storage as _default_db_storage


class MarketPortfolioMonteCarloVarReporter:
    def __init__(self, db_storage=None, market_portfolio_stress_monte_carlo_engine=None, market_portfolio_visualizer_v2=None):
        self.db_storage = db_storage if db_storage is not None else _default_db_storage
        self.monte_carlo_engine = market_portfolio_stress_monte_carlo_engine if market_portfolio_stress_monte_carlo_engine is not None else MarketPortfolioStressMonteCarloEngine()
        self.visualizer = market_portfolio_visualizer_v2

    def _calculate_var_and_es(self, simulations, confidence_level):
        if not simulations:
            raise ZeroDivisionError("Simulations list cannot be empty.")
        sims_sorted = sorted(simulations)
        index = int((1.0 - confidence_level) * len(sims_sorted))
        if index >= len(sims_sorted):
            index = len(sims_sorted) - 1
        var_value = sims_sorted[index]
        tail = sims_sorted[:index + 1]
        expected_shortfall = sum(tail) / len(tail) if tail else var_value
        return float(var_value), float(expected_shortfall)

    def generate_report(self, portfolio_id, confidence_level=0.95, time_horizon=1, simulations_count=1000):
        portfolio = self.db_storage.fetch_portfolio(portfolio_id)
        if portfolio is None:
            raise ValueError(f"Portfolio with ID {portfolio_id} not found.")

        mc_result = self.monte_carlo_engine.run_simulations(
            portfolio_id=portfolio_id,
            runs=simulations_count,
            time_horizon=time_horizon,
            confidence=confidence_level
        )

        simulations = mc_result.get("simulations", [])
        var_value, expected_shortfall = self._calculate_var_and_es(simulations, confidence_level)

        report_id = str(uuid.uuid4())
        report = {
            "report_id": report_id,
            "portfolio_id": portfolio_id,
            "confidence_level": confidence_level,
            "time_horizon": time_horizon,
            "var_value": var_value,
            "expected_shortfall": expected_shortfall,
            "simulation_id": mc_result.get("simulation_id")
        }

        self.db_storage.save_report(report)
        return report

    def export_report_to_webhook(self, report_id, target_url):
        stream = self.db_storage.get_report_stream(report_id)
        response = requests.post(target_url, data=stream.read())
        return response.status_code == 200

    def generate_distribution_plot(self, simulations):
        return self.visualizer.plot_distribution(simulations)


def market_portfolio_monte_carlo_var_reporter(payload):
    if not isinstance(payload, dict):
        payload = {}
    portfolio_id = payload.get("portfolio_id")
    simulation_id = payload.get("simulation_id")

    engine = MarketPortfolioStressMonteCarloEngine()
    engine_result = engine.run({
        "portfolio_id": portfolio_id,
        "runs": 1000,
        "confidence": 0.95,
        "simulation_id": simulation_id
    })

    sims = engine_result.get("simulations", [])
    if sims:
        sims_sorted = sorted(sims)
        index = int((1.0 - 0.95) * len(sims_sorted))
        if index >= len(sims_sorted):
            index = len(sims_sorted) - 1

        var_val = float(sims_sorted[index])
        tail = sims_sorted[:index + 1]
        es_val = float(sum(tail) / len(tail)) if tail else var_val
    else:
        var_val = 0.0
        es_val = 0.0

    report_result = {
        "report_id": str(uuid.uuid4()),
        "portfolio_id": portfolio_id,
        "simulation_id": engine_result.get("simulation_id", simulation_id),
        "confidence_level": 0.95,
        "time_horizon": 1,
        "var_value": var_val,
        "expected_shortfall": es_val
    }

    _default_db_storage({
        "action": "save",
        "table": "monte_carlo_var_reports",
        "data": report_result,
        "portfolio_id": portfolio_id
    })

    return report_result


def start_new(payload):
    return market_portfolio_monte_carlo_var_reporter(payload)
