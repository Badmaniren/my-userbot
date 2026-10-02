import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_deep_inspector_v3 import (
    market_portfolio_stress_deep_inspector_v3,
    market_portfolio_scenario_simulator,
    market_portfolio_var_liquidity_core,
    market_portfolio_stress_monte_carlo_engine,
    db_storage
)

class TestMarketPortfolioStressDeepInspectorV3Integration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulation_seed = random.randint(1000, 99999)
        self.stress_level = round(random.uniform(0.1, 0.9), 4)

    def test_deep_inspector_end_to_end_flow(self):
        # 1. Подготовка базовых данных через реальный модуль хранения/симуляции
        initial_state = {
            "portfolio_id": self.portfolio_id,
            "seed": self.simulation_seed,
            "stress_multiplier": self.stress_level,
            "assets": [
                {"ticker": "BTC", "volume": round(random.uniform(1.0, 10.0), 4)},
                {"ticker": "ETH", "volume": round(random.uniform(10.0, 50.0), 4)}
            ]
        }

        # Сохраняем начальное состояние в БД
        db_storage.save_portfolio_state(self.portfolio_id, initial_state)

        # 2. Прогоняем сценарий через симулятор
        simulation_result = market_portfolio_scenario_simulator.run_scenario(
            portfolio_id=self.portfolio_id,
            severity=self.stress_level
        )
        self.assertIsNotNone(simulation_result)

        # 3. Рассчитываем VaR и ликвидность
        var_liquidity_data = market_portfolio_var_liquidity_core.calculate(
            portfolio_id=self.portfolio_id,
            sim_data=simulation_result
        )
        self.assertIn("var_value", var_liquidity_data)

        # 4. Запускаем Монте-Карло для стресс-теста
        mc_output = market_portfolio_stress_monte_carlo_engine.execute(
            portfolio_id=self.portfolio_id,
            iterations=100,
            seed=self.simulation_seed
        )
        self.assertIsNotNone(mc_output)

        # 5. Вызываем целевой тестируемый модуль глубокого инспектирования уязвимостей
        inspection_report = market_portfolio_stress_deep_inspector_v3.inspect_vulnerabilities(
            portfolio_id=self.portfolio_id,
            simulation_ref=simulation_result,
            var_ref=var_liquidity_data,
            monte_carlo_ref=mc_output
        )

        # Проверяем возвращаемые данные на соответствие нашему случайно сгенерированному портфелю
        self.assertEqual(inspection_report["portfolio_id"], self.portfolio_id)
        self.assertIn("vulnerability_score", inspection_report)
        self.assertIsInstance(inspection_report["vulnerability_score"], float)

        # 6. Проверяем реальное побочное действие (появление артефакта/отчета в хранилище)
        report_path = f"reports/stress_inspection_{self.portfolio_id}.json"

        # Если модуль сохраняет отчет на диск, проверяем его создание и содержимое
        if os.path.exists(report_path):
            self.assertTrue(os.path.getsize(report_path) > 0)
            os.remove(report_path)
        else:
            # Альтернативная проверка через db_storage, если файлы не пишутся на диск
            stored_report = db_storage.get_inspection_report(self.portfolio_id)
            self.assertEqual(stored_report["portfolio_id"], self.portfolio_id)

if __name__ == "__main__":
    unittest.main()