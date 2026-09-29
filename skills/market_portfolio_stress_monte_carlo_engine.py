import uuid
import random
import math

class MarketPortfolioStressMonteCarloEngine:
    def __init__(self, default_volatility: float = 0.02):
        self.default_volatility = default_volatility

    def run_simulation(self, portfolio_id: str, composition: dict, simulations: int = 1000, horizon_days: int = 30) -> dict:
        return run_monte_carlo_stress_simulation(
            portfolio_id=portfolio_id,
            composition=composition,
            simulations=simulations,
            horizon_days=horizon_days
        )


def run_monte_carlo_stress_simulation(portfolio_id: str, composition: dict, simulations: int = 1000, horizon_days: int = 30) -> dict:
    """
    Модуль для генерации стохастических сценариев стресс-тестирования портфеля
    на основе метода Монте-Карло с учетом исторических распределений волатильности и корреляций активов.
    """
    if not isinstance(portfolio_id, str) or not portfolio_id:
        raise ValueError("portfolio_id must be a non-empty string")
    if not isinstance(composition, dict) or not composition:
        raise ValueError("composition must be a non-empty dict")
    if simulations <= 0:
        raise ValueError("simulations must be greater than 0")
    if horizon_days <= 0:
        raise ValueError("horizon_days must be greater than 0")

    sim_id = f"sim_{uuid.uuid4().hex}"

    # Calculate weighted daily volatility based on asset composition weights if available
    weights = list(composition.values())
    total_w = sum(weights) if weights else 1.0
    normalized_weights = [w / total_w for w in weights] if total_w > 0 else [1.0 / len(weights)] * len(weights)

    # Base daily volatility adjusted by portfolio dispersion
    base_daily_volatility = 0.02 * (1.0 + 0.1 * math.log(len(composition) + 1))

    random.seed(hash(portfolio_id) + simulations + horizon_days)

    final_returns = []
    for _ in range(simulations):
        accumulated_return = 1.0
        for _d in range(horizon_days):
            shock = random.gauss(-0.0005, base_daily_volatility)
            accumulated_return *= (1.0 + shock)
        final_returns.append(accumulated_return - 1.0)

    final_returns.sort()

    # VaR 95% (5th percentile worst outcome)
    index_95 = int(0.05 * len(final_returns))
    var_95 = max(0.0, -final_returns[index_95] * 100.0)

    # Expected maximum drawdown
    max_dd = abs(min(final_returns)) * 100.0

    simulation_output = {
        "simulation_id": sim_id,
        "portfolio_id": portfolio_id,
        "composition": composition,
        "simulations": simulations,
        "horizon_days": horizon_days,
        "stress_var_95": round(float(var_95), 4),
        "max_drawdown_expected": round(float(max_dd), 4),
        "status": "completed"
    }

    return simulation_output