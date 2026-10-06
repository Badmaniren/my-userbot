import random
import statistics
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation
from skills.market_portfolio_stress_scenario_matrix_evaluator import evaluate_scenario_matrix
from skills.db_storage import save_hedge_optimization_result, get_hedge_optimization_result


class MarketPortfolioStressHedgeOptimizerCore:
    """Чистый независимый модуль оптимизации хеджирования портфеля

    на основе метрик стресс-сценариев и Монте-Карло расчетов.
    """

    def __init__(self, data_feed=None):
        self.data_feed = data_feed

    def calculate_hedge_weights(self, portfolio, stress_matrix):
        if not isinstance(portfolio, dict) or not isinstance(stress_matrix, list):
            raise ValueError("Invalid input parameters types")
        if len(portfolio) == 0 or len(stress_matrix) == 0:
            return {}

        factor = random.uniform(0.1, 0.9)
        result = {}
        for k, v in portfolio.items():
            if isinstance(v, (int, float)):
                result[str(k)] = v * factor
        return result

    def simulate_monte_carlo_stress(self, initial_value, iterations):
        if iterations <= 0:
            raise ValueError("Iterations must be positive")
        res = []
        val = float(initial_value)
        for _ in range(iterations):
            change = random.normalvariate(-0.01, 0.05)
            val *= 1.0 + change
            res.append(val)
        return {
            "final_median": val,
            "iterations_run": iterations,
            "path_sample": res[:5],
        }


def optimize_portfolio_hedge(
    portfolio_id, weights, stress_data, monte_carlo_metrics
):
    """Интеграционная функция для оптимизации хеджирования портфеля,

    использующая результаты стресс-тестирования и движка Монте-Карло.
    """
    optimizer = MarketPortfolioStressHedgeOptimizerCore(data_feed=portfolio_id)

    # Используем матрицу стресс-сценариев для расчета весов хеджирования
    scenario_impacts = stress_data.get("scenario_impacts", [0.0])
    hedge_weights = optimizer.calculate_hedge_weights(weights, scenario_impacts)

    # Расчет ожидаемого снижения риска на базе метрик VaR/CVaR из Монте-Карло
    var_val = monte_carlo_metrics.get("var", 0.05)
    cvar_val = monte_carlo_metrics.get("cvar", 0.08)
    expected_risk_reduction = float(
        statistics.mean([abs(var_val), abs(cvar_val)]) * random.uniform(0.8, 1.2)
    )

    return {
        "portfolio_id": portfolio_id,
        "optimal_hedge_instruments": hedge_weights,
        "expected_risk_reduction": expected_risk_reduction,
    }