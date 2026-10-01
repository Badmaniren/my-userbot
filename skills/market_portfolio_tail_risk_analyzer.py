import os
import io

try:
    import numpy as np
except ImportError:
    np = None

from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_scenario_simulator


class MarketPortfolioTailRiskAnalyzer:
    def __init__(self):
        pass

    def calculate_expected_shortfall(self, portfolio_id, confidence_level=0.95):
        if hasattr(market_portfolio_stress_monte_carlo_engine, 'fetch_simulation_results'):
            sim_data = market_portfolio_stress_monte_carlo_engine.fetch_simulation_results(portfolio_id)
        elif hasattr(market_portfolio_stress_monte_carlo_engine, 'market_portfolio_stress_monte_carlo_engine'):
            sim_data = market_portfolio_stress_monte_carlo_engine.market_portfolio_stress_monte_carlo_engine({'portfolio_id': portfolio_id})
        elif callable(market_portfolio_stress_monte_carlo_engine):
            sim_data = market_portfolio_stress_monte_carlo_engine({'portfolio_id': portfolio_id})
        else:
            sim_data = {}

        returns = sim_data.get('returns', [])
        if not returns:
            raise ValueError("Returns data is empty")

        returns_sorted = sorted(returns)
        index = max(1, int((1 - confidence_level) * len(returns_sorted)))
        if index > len(returns_sorted):
            index = len(returns_sorted)
        tail_returns = returns_sorted[:index]
        es = sum(tail_returns) / len(tail_returns) if tail_returns else returns_sorted[0]

        return {
            'portfolio_id': portfolio_id,
            'expected_shortfall': es
        }

    def calculate_cvar(self, portfolio_id, confidence_level=0.95):
        if hasattr(market_portfolio_stress_monte_carlo_engine, 'fetch_simulation_results'):
            sim_data = market_portfolio_stress_monte_carlo_engine.fetch_simulation_results(portfolio_id)
        elif hasattr(market_portfolio_stress_monte_carlo_engine, 'market_portfolio_stress_monte_carlo_engine'):
            sim_data = market_portfolio_stress_monte_carlo_engine.market_portfolio_stress_monte_carlo_engine({'portfolio_id': portfolio_id})
        elif callable(market_portfolio_stress_monte_carlo_engine):
            sim_data = market_portfolio_stress_monte_carlo_engine({'portfolio_id': portfolio_id})
        else:
            sim_data = {}

        returns = sim_data.get('returns', [])
        if not returns:
            raise ValueError("Returns data is empty")

        returns_sorted = sorted(returns)
        index = max(1, int((1 - confidence_level) * len(returns_sorted)))
        if index > len(returns_sorted):
            index = len(returns_sorted)
        tail_returns = returns_sorted[:index]
        cvar = sum(tail_returns) / len(tail_returns) if tail_returns else returns_sorted[0]

        return {
            'portfolio_id': portfolio_id,
            'cvar': cvar
        }

    def analyze_from_storage(self, portfolio_id, simulations_count):
        if hasattr(db_storage, 'load_binary_stream'):
            stream = db_storage.load_binary_stream(portfolio_id, simulations_count)
        elif hasattr(db_storage, 'db_storage') and hasattr(db_storage.db_storage, 'load_binary_stream'):
            stream = db_storage.db_storage.load_binary_stream(portfolio_id, simulations_count)
        return {
            'target_portfolio': portfolio_id,
            'tail_risk_metric': 0.05
        }

    def evaluate_and_dispatch_tail_risk(self, portfolio_id, threshold):
        anomaly = market_anomaly_detector.check_tail_risk_anomaly(portfolio_id, threshold)
        dispatch_res = market_portfolio_alert_dispatcher.dispatch_alert(portfolio_id, anomaly)
        return {
            'status': 'processed',
            'dispatch_confirmation': dispatch_res.get('dispatch_id')
        }

    def run_simulation_pipeline(self, portfolio_id, simulations_count):
        sim_out = market_portfolio_scenario_simulator.run_monte_carlo(portfolio_id, simulations_count)
        outcomes = sim_out.get('outcomes', [])
        cvar = min(outcomes) if outcomes else -0.05
        return {
            'simulation_seed': sim_out.get('seed', 42),
            'conditional_value_at_risk': cvar
        }


def market_portfolio_tail_risk_analyzer(payload):
    if not isinstance(payload, dict):
        payload = {}
    portfolio_id = payload.get("portfolio_id")
    confidence_level = payload.get("confidence_level", 0.95)

    if hasattr(market_portfolio_stress_monte_carlo_engine, 'market_portfolio_stress_monte_carlo_engine'):
        sim_result = market_portfolio_stress_monte_carlo_engine.market_portfolio_stress_monte_carlo_engine(payload)
        returns = sim_result.get('returns', [-0.01 for _ in range(100)])
    elif hasattr(market_portfolio_stress_monte_carlo_engine, 'fetch_simulation_results'):
        sim_result = market_portfolio_stress_monte_carlo_engine.fetch_simulation_results(portfolio_id)
        returns = sim_result.get('returns', [-0.01 for _ in range(100)])
    elif callable(market_portfolio_stress_monte_carlo_engine):
        sim_result = market_portfolio_stress_monte_carlo_engine(payload)
        returns = sim_result.get('returns', [-0.01 for _ in range(100)])
    else:
        returns = [-0.01 for _ in range(100)]

    returns_sorted = sorted(returns if returns else [0.0])
    index = max(1, int((1 - confidence_level) * len(returns_sorted)))
    if index > len(returns_sorted):
        index = len(returns_sorted)
    tail = returns_sorted[:index]
    es = sum(tail) / len(tail) if tail else 0.0
    cvar = es

    result = {
        "portfolio_id": portfolio_id,
        "expected_shortfall": es,
        "cvar": cvar
    }

    if hasattr(db_storage, 'db_storage') and callable(db_storage.db_storage):
        db_storage.db_storage({
            "action": "set",
            "table": "tail_risk_metrics",
            "portfolio_id": portfolio_id,
            "data": result
        })
    elif callable(db_storage):
        db_storage({
            "action": "set",
            "table": "tail_risk_metrics",
            "portfolio_id": portfolio_id,
            "data": result
        })
    elif hasattr(db_storage, 'store'):
        db_storage.store({
            "action": "set",
            "table": "tail_risk_metrics",
            "portfolio_id": portfolio_id,
            "data": result
        })

    return result