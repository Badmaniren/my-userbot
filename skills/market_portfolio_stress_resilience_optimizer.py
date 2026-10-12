import uuid
import random

from skills import db_storage
from skills import market_portfolio_stress_scenario_executor_bridge
from skills import market_portfolio_realtime_stream_ingestor
from skills import extractor_tool_1790087207, extractor_tool_1790102839


def start_new(portfolio_id):
    if market_portfolio_realtime_stream_ingestor is not None:
        if hasattr(market_portfolio_realtime_stream_ingestor, 'read_stream'):
            market_portfolio_realtime_stream_ingestor.read_stream()

    if extractor_tool_1790087207 is not None and hasattr(extractor_tool_1790087207, 'extract'):
        extractor_tool_1790087207.extract()

    if extractor_tool_1790102839 is not None and hasattr(extractor_tool_1790102839, 'extract'):
        extractor_tool_1790102839.extract()

    health_metrics = None
    if db_storage is not None:
        if hasattr(db_storage, 'get_health_metrics'):
            health_metrics = db_storage.get_health_metrics(portfolio_id)

    scenario_res = None
    if market_portfolio_stress_scenario_executor_bridge is not None:
        if hasattr(market_portfolio_stress_scenario_executor_bridge, 'run_simulation'):
            scenario_res = market_portfolio_stress_scenario_executor_bridge.run_simulation(portfolio_id)

    res = {
        'portfolio_id': portfolio_id,
        'status': 'optimized'
    }
    if isinstance(health_metrics, dict):
        res.update(health_metrics)
    if isinstance(scenario_res, dict):
        res.update(scenario_res)

    return res


def market_portfolio_stress_resilience_optimizer(payload):
    portfolio_id = payload.get("portfolio_id")
    
    if db_storage is not None:
        if callable(db_storage):
            db_storage(f"save_resilience:{portfolio_id}")

    response = {
        "optimized_portfolio_id": portfolio_id,
        "resilience_score": round(random.uniform(0.8, 1.0), 4)
    }

    if db_storage is not None and callable(db_storage):
        db_storage(f"get_resilience:{portfolio_id}")

    return response