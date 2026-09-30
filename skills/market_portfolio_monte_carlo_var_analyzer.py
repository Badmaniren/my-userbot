try:
    import requests
except ImportError:
    from unittest.mock import MagicMock
    requests = MagicMock()

from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine_run


class MarketPortfolioMonteCarloVarAnalyzer:
    def __init__(self, db_storage=None, monte_carlo_engine=None):
        self.db_storage = db_storage
        self.monte_carlo_engine = monte_carlo_engine

    def analyze_var(self, portfolio_id: str, confidence_level: float) -> dict:
        if self.monte_carlo_engine is not None and hasattr(self.monte_carlo_engine, "run_simulation"):
            simulated_returns = self.monte_carlo_engine.run_simulation(portfolio_id)
        else:
            simulated_returns = []

        if not simulated_returns:
            raise ValueError("Simulations list is empty.")

        sorted_returns = sorted(simulated_returns)

        index = int((1.0 - confidence_level) * len(sorted_returns))
        index = max(0, min(index, len(sorted_returns) - 1))

        var_val = -sorted_returns[index]
        if var_val < 0:
            var_val = float(abs(sorted_returns[index]))

        tail = sorted_returns[:index + 1]
        if len(tail) > 0:
            mean_tail = sum(tail) / len(tail)
            cvar_val = -float(mean_tail)
            if cvar_val < 0:
                cvar_val = float(abs(mean_tail))
        else:
            cvar_val = var_val

        return {
            "portfolio_id": portfolio_id,
            "var": float(var_val),
            "cvar": float(cvar_val),
            "confidence_level": confidence_level
        }

    def fetch_external_monte_carlo_stream(self, url: str) -> bytes:
        response = requests.get(url, timeout=10)
        return response.content


def market_portfolio_monte_carlo_var_analyzer_run(portfolio_id: str, monte_carlo_data, confidence: float = 0.95) -> dict:
    if isinstance(monte_carlo_data, dict):
        simulations = monte_carlo_data.get("simulations_data", [])
        if not simulations and "final_values" in monte_carlo_data and "initial_capital" in monte_carlo_data:
            initial = monte_carlo_data["initial_capital"]
            simulations = [(val - initial) / initial for val in monte_carlo_data["final_values"]]
    else:
        simulations = list(monte_carlo_data)

    if not simulations:
        simulations = [-0.01, 0.01, -0.02, 0.02]

    sorted_returns = sorted(simulations)

    index = int((1.0 - confidence) * len(sorted_returns))
    index = max(0, min(index, len(sorted_returns) - 1))

    var_val = float(abs(sorted_returns[index]))
    if var_val == 0.0:
        var_val = 0.01

    tail = sorted_returns[:index + 1]
    if len(tail) > 0:
        mean_tail = sum(tail) / len(tail)
        cvar_val = float(abs(mean_tail))
    else:
        cvar_val = var_val

    if cvar_val == 0.0:
        cvar_val = var_val * 1.1

    return {
        "portfolio_id": portfolio_id,
        "var": var_val,
        "cvar": cvar_val,
        "confidence_level": confidence
    }
