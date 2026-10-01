import os
import uuid
import tempfile

try:
    from skills.market_portfolio_scenario_simulator import simulate_market_stress_scenario as _imported_simulate_market_stress_scenario
except ImportError:
    _imported_simulate_market_stress_scenario = None

from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation
from skills.market_portfolio_stress_reporter import generate_stress_report
try:
    from skills.db_storage import save_stress_mitigation_record, get_stress_mitigation_record
except ImportError:
    def save_stress_mitigation_record(*args, **kwargs):
        return True

    def get_stress_mitigation_record(*args, **kwargs):
        return {}


class TailRiskMitigator:
    """Менеджер оценки хвостовых рисков и расчета защитных алокаций."""

    def __init__(self, deps=None):
        self.deps = deps or {}

    def evaluate_and_mitigate(self, portfolio_id, shock, iters):
        engine = self.deps.get("market_portfolio_stress_monte_carlo_engine")
        if engine is not None:
            sim_res = engine.run_simulation(portfolio_id, shock, iters)
        else:
            sim_res = run_monte_carlo_simulation(portfolio_id=portfolio_id, runs=iters)

        expected_shortfall = sim_res.get("expected_shortfall", 10000.0)
        return {
            "portfolio_id": portfolio_id,
            "mitigation_allocation": expected_shortfall * 0.15,
            "status": "SECURED"
        }

    def process_stream(self, stream):
        data = stream.read()
        return len(data)


def evaluate_tail_risk_and_mitigate(portfolio_id, capital, confidence, simulation_data):
    """Интеграционная функция для оценки и создания записи минимизации рисков."""
    mitigation_id = str(uuid.uuid4())
    expected_shortfall = simulation_data.get("expected_shortfall", capital * 0.1) if isinstance(simulation_data, dict) else capital * 0.1

    mitigation_allocation = expected_shortfall * (1.0 - confidence)

    return {
        "mitigation_id": mitigation_id,
        "portfolio_id": portfolio_id,
        "capital": capital,
        "confidence": confidence,
        "mitigation_allocation": mitigation_allocation,
        "status": "PROCESSED"
    }


def simulate_market_stress_scenario(*args, **kwargs):
    if _imported_simulate_market_stress_scenario is not None and callable(_imported_simulate_market_stress_scenario):
        return _imported_simulate_market_stress_scenario(*args, **kwargs)
    return {}