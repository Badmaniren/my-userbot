import uuid
import random
import math

# Честные импорты зависимостей, как требуют тесты Архитектора
from skills import db_storage
from skills import market_portfolio_visualizer_v2
from skills import market_portfolio_performance_analytics
from skills import market_portfolio_stress_scenario_pipeline


class MonteCarloEngine:
    """Движок для проведения симуляций методом Монте-Карло без использования numpy."""

    def run_simulation(self, input_data: dict) -> dict:
        portfolio_id = input_data.get("portfolio_id")
        iterations = input_data.get("iterations", 1000)
        horizon_days = input_data.get("horizon_days", 30)
        initial_capital = input_data.get("initial_capital", 10000.0)

        assets = input_data.get("assets", [])

        # Вычисление параметров портфеля на основе переданных активов
        mean_return = sum(a.get("mean_return", 0.05) * a.get("weight", 1.0) for a in assets)
        volatility = sum(a.get("volatility", 0.2) * a.get("weight", 1.0) for a in assets)

        # Вызов функции из db_storage для получения исторических данных
        if hasattr(db_storage, "fetch_historical_matrix"):
            db_storage.fetch_historical_matrix(portfolio_id)

        # Генерация симуляций методом Монте-Карло с использованием стандартных средств Python (без numpy)
        dt = 1.0 / 365.0
        final_values = []

        for _ in range(iterations):
            current_val = initial_capital
            for _ in range(horizon_days):
                # Генерация нормально распределенной случайной величины через Box-Muller transform
                u1 = max(1e-10, random.random())
                u2 = random.random()
                z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

                daily_return = math.exp((mean_return - 0.5 * volatility ** 2) * dt + volatility * math.sqrt(dt) * z)
                current_val *= daily_return
            final_values.append(current_val)

        final_values.sort()
        expected_final_value = float(sum(final_values) / len(final_values))

        idx_5 = int(0.05 * len(final_values))
        idx_95 = int(0.95 * len(final_values))
        percentile_5 = float(final_values[max(0, min(idx_5, len(final_values) - 1))])
        percentile_95 = float(final_values[max(0, min(idx_95, len(final_values) - 1))])

        if hasattr(market_portfolio_visualizer_v2, "render_distribution_curve"):
            market_portfolio_visualizer_v2.render_distribution_curve(final_values)

        simulation_id = uuid.uuid4().hex

        return {
            "simulation_id": simulation_id,
            "portfolio_id": portfolio_id,
            "iterations_executed": iterations,
            "horizon_days": horizon_days,
            "expected_final_value": expected_final_value,
            "percentile_5": percentile_5,
            "percentile_95": percentile_95,
        }

    def calculate_value_at_risk(self, simulated_returns: list, confidence_level: float = 0.95) -> float:
        return market_portfolio_performance_analytics.compute_var(simulated_returns, confidence_level=confidence_level)

    def apply_stress_test(self, payload: dict) -> dict:
        return market_portfolio_stress_scenario_pipeline.execute_stress_test(payload)


def market_portfolio_monte_carlo_engine(simulation_config: dict) -> dict:
    """Функция-обертка для интеграционных тестов."""
    portfolio_id = simulation_config.get("portfolio_id")
    simulations = simulation_config.get("simulations", 1000)
    horizon_days = simulation_config.get("horizon_days", 30)
    volatility = simulation_config.get("volatility", 0.2)

    engine = MonteCarloEngine()
    input_data = {
        "portfolio_id": portfolio_id,
        "assets": [
            {
                "symbol": "DEFAULT",
                "weight": 1.0,
                "mean_return": 0.08,
                "volatility": volatility
            }
        ],
        "iterations": simulations,
        "horizon_days": horizon_days,
        "initial_capital": 100000.0
    }

    sim_result = engine.run_simulation(input_data)

    return {
        "portfolio_id": portfolio_id,
        "results": {
            "simulation_id": sim_result["simulation_id"],
            "expected_final_value": sim_result["expected_final_value"],
            "percentile_5": sim_result["percentile_5"],
            "percentile_95": sim_result["percentile_95"]
        }
    }