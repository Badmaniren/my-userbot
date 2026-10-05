import random
import uuid

try:
    from skills.market_portfolio_stress_scenario_matrix_evaluator import (
        market_portfolio_stress_scenario_matrix_evaluator
    )
except ImportError:
    market_portfolio_stress_scenario_matrix_evaluator = None

try:
    from skills.market_portfolio_stress_monte_carlo_engine import (
        market_portfolio_stress_monte_carlo_engine
    )
except ImportError:
    market_portfolio_stress_monte_carlo_engine = None

from skills.db_storage import db_storage


class MarketPortfolioStressReportSynthesizer:
    def __init__(self, dependencies=None):
        self.deps = dependencies if dependencies is not None else {}

    def synthesize_report(self, portfolio_id, stress_matrix_data):
        if not portfolio_id or not stress_matrix_data:
            raise ValueError("Invalid input data for synthesis")

        storage = self.deps.get('db_storage', db_storage)
        report_id = stress_matrix_data.get("report_id") or uuid.uuid4().hex

        if storage and hasattr(storage, 'save_report'):
            storage.save_report(report_id, stress_matrix_data)
        elif storage and callable(storage):
            storage({
                "action": "save",
                "table": "stress_reports",
                "report_id": report_id,
                "data": stress_matrix_data
            })

        return {
            "report_id": report_id,
            "portfolio_id": portfolio_id,
            "status": "SYNTHESIZED",
            "entropy": random.random()
        }


def market_portfolio_stress_report_synthesizer(payload):
    if not payload or not isinstance(payload, dict):
        raise ValueError("Invalid input data for synthesis")

    portfolio_id = payload.get("portfolio_id")
    report_id = payload.get("report_id", f"rep_{uuid.uuid4().hex}")

    if not portfolio_id:
        raise ValueError("Invalid input data for synthesis")

    matrix_eval = payload.get("matrix_evaluation", {})
    mc_sim = payload.get("monte_carlo_simulation", {})

    if not matrix_eval and not mc_sim:
        raise ValueError("Invalid input data for synthesis")

    aggregated_metrics = {
        "matrix_status": matrix_eval.get("status", "EVALUATED"),
        "mc_simulations": mc_sim.get("iterations", 100),
        "mean_outcome": mc_sim.get("mean_outcome", 0.0)
    }

    result = {
        "report_id": report_id,
        "portfolio_id": portfolio_id,
        "status": "SYNTHESIZED",
        "entropy": random.random(),
        "aggregated_metrics": aggregated_metrics
    }

    if callable(db_storage):
        db_storage({
            "action": "save",
            "table": "stress_reports",
            "report_id": report_id,
            "data": result
        })

    return result
