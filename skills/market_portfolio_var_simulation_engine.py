from math import sqrt
from skills.db_storage import save_var_simulation_result, get_var_simulation_result
from skills.market_portfolio_valuation import calculate_portfolio_value
from skills.market_portfolio_collector_agent import collect_market_data


class MarketPortfolioVaRSimulationEngine:
    def __init__(self, db_storage=None, scenario_simulator=None):
        self.db_storage = db_storage
        self.scenario_simulator = scenario_simulator

    def calculate_historical_var(self, portfolio_id, returns_series, confidence_level=0.95):
        if not returns_series:
            raise ValueError("Returns series cannot be empty")
        sorted_returns = sorted(returns_series)
        index = int((1 - confidence_level) * len(sorted_returns))
        var = -sorted_returns[max(0, index)]
        return {
            "portfolio_id": portfolio_id,
            "var_historical": var,
            "confidence": confidence_level
        }

    def calculate_parametric_var(self, portfolio_id, mean, std_dev, confidence_level=0.95):
        z_score = 1.6448536269514722 if confidence_level >= 0.95 else 1.2815515655446004
        var = -(mean - z_score * std_dev)
        return {
            "portfolio_id": portfolio_id,
            "var_parametric": var,
            "confidence": confidence_level
        }


def simulate_portfolio_var(portfolio_id, valuation_data, confidence_level=0.95, horizon_days=1):
    total_value = valuation_data.get("total_value", 100000.0)

    returns_series = valuation_data.get("returns_series", [-0.02, -0.01, 0.005, 0.01, 0.015, -0.015, 0.002, -0.003, 0.008, -0.005])

    engine = MarketPortfolioVaRSimulationEngine()
    hist_result = engine.calculate_historical_var(portfolio_id, returns_series, confidence_level)

    mean = sum(returns_series) / len(returns_series) if returns_series else 0.0
    variance = sum((x - mean) ** 2 for x in returns_series) / len(returns_series) if returns_series else 0.01
    std_dev = sqrt(variance)

    param_result = engine.calculate_parametric_var(portfolio_id, mean, std_dev, confidence_level)

    horizon_factor = sqrt(horizon_days)
    var_hist = hist_result["var_historical"] * total_value * horizon_factor
    var_param = param_result["var_parametric"] * total_value * horizon_factor

    simulation_result = {
        "simulation_id": valuation_data.get("simulation_id", portfolio_id),
        "portfolio_id": portfolio_id,
        "var_historical": var_hist,
        "var_parametric": var_param,
        "confidence_level": confidence_level,
        "horizon_days": horizon_days
    }

    save_var_simulation_result(simulation_result)
    return simulation_result
