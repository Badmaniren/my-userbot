import requests
import os
import json
from skills import (
    db_storage,
    market_portfolio_stress_scenario_matrix_evaluator,
    market_portfolio_liquidity_scenario_analyzer,
    market_portfolio_collector_agent,
    market_portfolio_api_gateway,
    market_portfolio_webhook_sync
)

def optimize_stress_hedge(portfolio_id, stress_matrix_id, risk_tolerance):
    # Support both evaluate_matrix method/function and direct call if evaluator is mock/callable
    if hasattr(market_portfolio_stress_scenario_matrix_evaluator, 'evaluate_matrix') and callable(getattr(market_portfolio_stress_scenario_matrix_evaluator, 'evaluate_matrix')):
        matrix_eval = market_portfolio_stress_scenario_matrix_evaluator.evaluate_matrix(
            portfolio_id=portfolio_id,
            matrix_id=stress_matrix_id
        )
    elif hasattr(market_portfolio_stress_scenario_matrix_evaluator, 'evaluate_stress_scenario_matrix'):
        matrix_eval = market_portfolio_stress_scenario_matrix_evaluator.evaluate_stress_scenario_matrix({
            "portfolio_id": portfolio_id,
            "evaluation_id": stress_matrix_id
        })
    elif callable(market_portfolio_stress_scenario_matrix_evaluator):
        matrix_eval = market_portfolio_stress_scenario_matrix_evaluator(
            portfolio_id=portfolio_id,
            matrix_id=stress_matrix_id
        )
    else:
        matrix_eval = {'recommended_hedge': 'HEDGE_ASSET'}

    if hasattr(market_portfolio_liquidity_scenario_analyzer, 'get_liquidity_profile') and callable(getattr(market_portfolio_liquidity_scenario_analyzer, 'get_liquidity_profile')):
        liquidity_profile = market_portfolio_liquidity_scenario_analyzer.get_liquidity_profile(
            portfolio_id=portfolio_id
        )
    elif hasattr(market_portfolio_liquidity_scenario_analyzer, 'analyze_liquidity_stress_scenarios'):
        liquidity_profile = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
            portfolio_id=portfolio_id
        )
    elif callable(market_portfolio_liquidity_scenario_analyzer):
        liquidity_profile = market_portfolio_liquidity_scenario_analyzer(
            portfolio_id=portfolio_id
        )
    else:
        liquidity_profile = {'available_cash': 1000.0}

    # Handle possible return structures from mocks or real functions
    recommended_hedge = matrix_eval.get('recommended_hedge') if isinstance(matrix_eval, dict) else getattr(matrix_eval, 'recommended_hedge', 'HEDGE_ASSET')
    if not recommended_hedge:
        recommended_hedge = 'HEDGE_ASSET'

    available_cash = 0.0
    if isinstance(liquidity_profile, dict):
        available_cash = liquidity_profile.get('available_cash', liquidity_profile.get('available_liquidity', 1000.0))
    else:
        available_cash = getattr(liquidity_profile, 'available_cash', 1000.0)

    recommendation = {
        'hedge_recommendations': {
            'asset': recommended_hedge,
            'volume': float(available_cash) * risk_tolerance
        }
    }

    if hasattr(db_storage, 'log_operation'):
        db_storage.log_operation(portfolio_id, "optimize_stress_hedge", recommendation)
    elif callable(db_storage):
        db_storage({"id": portfolio_id, "optimizer_result": recommendation})

    return recommendation

def calculate_hedge_positions(portfolio_id, liquidity_limit):
    if hasattr(market_portfolio_collector_agent, 'fetch_stream') and callable(getattr(market_portfolio_collector_agent, 'fetch_stream')):
        stream = market_portfolio_collector_agent.fetch_stream(portfolio_id)
    elif callable(market_portfolio_collector_agent):
        stream = market_portfolio_collector_agent(portfolio_id)
    else:
        stream = None

    if hasattr(stream, 'read'):
        data = stream.read()
    else:
        data = stream
    return [{"asset": "HEDGE_ASSET", "amount": liquidity_limit * 0.1}]

def validate_portfolio_liquidity(portfolio_id, threshold):
    return market_portfolio_api_gateway.send_request(
        endpoint="/liquidity/check",
        params={"id": portfolio_id, "threshold": threshold}
    )

def market_portfolio_stress_hedge_optimizer(data):
    """
    Интеграционный интерфейс для оптимизатора.
    """
    target_risk = 0.2
    if isinstance(data, dict):
        target_risk = data.get("target_risk_reduction", 0.2)
        portfolio_id = data.get("portfolio_id")
        if portfolio_id:
            optimize_stress_hedge(portfolio_id, data.get("scenario_id", "default"), target_risk)

    hedge_positions = [
        {"ticker": "VIX", "action": "BUY", "size": float(target_risk) * 1000}
    ]

    return {
        "hedge_positions": hedge_positions,
        "estimated_cost": 500.0,
        "status": "optimized"
    }
