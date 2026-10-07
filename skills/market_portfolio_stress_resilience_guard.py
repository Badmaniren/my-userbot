import io
import random
import uuid

from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine


def start_new(dependencies, seed=None):
    if seed is not None:
        random.seed(seed)

    mc_engine = dependencies.get("market_portfolio_stress_monte_carlo_engine")
    pipeline = dependencies.get("market_portfolio_stress_scenario_pipeline")

    if pipeline:
        eval_res = pipeline.evaluate()
        if eval_res and eval_res.get("status") == "FAILED":
            reason = eval_res.get("reason", "validation_failed")
            raise ValueError(reason)

    if mc_engine:
        simulation_result = mc_engine.run_simulation()
        if simulation_result:
            return simulation_result

    return None


def market_portfolio_stress_resilience_guard(portfolio_id, simulation_metrics):
    resilience_status = "SECURE"
    for metric in simulation_metrics:
        if isinstance(metric, dict) and metric.get("value", 0) < 0:
            resilience_status = "VULNERABLE"

    result = {
        "portfolio_id": portfolio_id,
        "resilience_status": resilience_status,
        "metrics_count": len(simulation_metrics)
    }

    db_storage(
        action="set",
        key=f"resilience_{portfolio_id}",
        value=result
    )

    return result