import unittest
import uuid
import random
import os

from skills.market_portfolio_hedge_signal_engine import (
    generate_hedge_signals,
)
from skills.market_portfolio_scenario_simulator import (
    simulate_stress_scenarios,
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    run_monte_carlo_stress_simulation,
)
from skills.market_portfolio_var_liquidity_core import (
    calculate_var_liquidity,
)
from skills.db_storage import (
    save_portfolio_data,
    get_portfolio_data,
)


class IntegrationTestMarketPortfolioHedgeSignalEngine(unittest.TestCase):

    def test_hedge_signal_engine_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        volatility_factor = round(random.uniform(0.1, 0.5), 4)

        portfolio_payload = {
            "portfolio_id": portfolio_id,
            "capital": initial_capital,
            "volatility": volatility_factor,
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "value": initial_capital * 0.5},
                {"ticker": "TSLA", "weight": 0.5, "value": initial_capital * 0.5}
            ]
        }

        save_success = save_portfolio_data(portfolio_id, portfolio_payload)
        self.assertTrue(save_success, "Не удалось сохранить тестовый портфель в БД")

        retrieved_data = get_portfolio_data(portfolio_id)
        self.assertIsNotNone(retrieved_data, "Данные портфеля не найдены в БД")

        simulation_result = simulate_stress_scenarios(portfolio_id, retrieved_data)
        self.assertIsInstance(simulation_result, dict)
        self.assertIn("scenario_id", simulation_result)

        monte_carlo_result = run_monte_carlo_stress_simulation(portfolio_id, simulation_result)
        self.assertIsInstance(monte_carlo_result, dict)

        var_liquidity_metrics = calculate_var_liquidity(portfolio_id, monte_carlo_result)
        self.assertIsInstance(var_liquidity_metrics, dict)

        hedge_signals = generate_hedge_signals(
            portfolio_id=portfolio_id,
            simulation_data=simulation_result,
            monte_carlo_data=monte_carlo_result,
            var_data=var_liquidity_metrics
        )

        self.assertIsInstance(hedge_signals, dict, "Результат генерации сигналов должен быть словарем")
        self.assertIn("hedge_signal_id", hedge_signals, "Должен генерироваться уникальный ID сигнала хеджирования")
        self.assertEqual(hedge_signals["portfolio_id"], portfolio_id, "ID портфеля в сигнале должен совпадать")
        self.assertIsInstance(hedge_signals.get("recommended_actions"), list, "Рекомендации должны быть списком")
        self.assertGreater(len(hedge_signals["recommended_actions"]), 0, "Список рекомендаций хеджирования не должен быть пустым")

        signal_file_path = f"hedge_signal_{portfolio_id}.json"
        self.assertTrue(os.path.exists(signal_file_path), "Сигнал должен сохраняться в файловую систему или артефакт")

        if os.path.exists(signal_file_path):
            os.remove(signal_file_path)


if __name__ == "__main__":
    unittest.main()