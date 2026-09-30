import numpy as np
from skills import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_monte_carlo_engine import run_stress_monte_carlo_simulation
from skills.db_storage import save_portfolio_risk_metrics, get_portfolio_risk_metrics

def _compute_var_and_es(losses, confidence_level=0.95):
    if not losses:
        return 0.0, 0.0

    losses_arr = np.array(losses, dtype=float)
    sorted_losses = np.sort(losses_arr)

    n = len(sorted_losses)
    index = int(np.ceil(confidence_level * n)) - 1
    index = max(0, min(index, n - 1))

    var_val = float(sorted_losses[index])

    tail_losses = sorted_losses[index:]
    if len(tail_losses) > 0:
        es_val = float(np.mean(tail_losses))
    else:
        es_val = var_val

    return var_val, es_val

def calculate_portfolio_var(portfolio_data, confidence_level=0.95, simulations=1000, data_stream=None):
    portfolio_id = portfolio_data.get("portfolio_id") if isinstance(portfolio_data, dict) else None

    if data_stream is not None:
        data_stream.read()

    engine_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress(
        portfolio_data=portfolio_data,
        simulations=simulations
    )

    loss_distribution = engine_result.get("portfolio_loss_distribution", [])

    var_val, es_val = _compute_var_and_es(loss_distribution, confidence_level=confidence_level)

    return {
        "portfolio_id": portfolio_id,
        "var": var_val,
        "expected_shortfall": es_val
    }

def start_new(payload: dict = None, **kwargs) -> dict:
    if payload is None:
        payload = {}
    portfolio_data = payload.get("portfolio_data", payload)
    confidence = payload.get("confidence_level", payload.get("confidence", 0.95))
    simulations = payload.get("simulations", 1000)
    return calculate_portfolio_var(
        portfolio_data=portfolio_data,
        confidence_level=confidence,
        simulations=simulations
    )

def market_portfolio_monte_carlo_var_calculator(payload: dict = None, **kwargs) -> dict:
    return start_new(payload, **kwargs)

def calculate_monte_carlo_var_and_es(portfolio_id, confidence=0.95, simulations_data=None):
    losses = []
    if isinstance(simulations_data, dict):
        losses = simulations_data.get("portfolio_loss_distribution", [])
    elif isinstance(simulations_data, list):
        losses = simulations_data

    var_val, es_val = _compute_var_and_es(losses, confidence_level=confidence)

    return {
        "portfolio_id": portfolio_id,
        "var": var_val,
        "expected_shortfall": es_val
    }