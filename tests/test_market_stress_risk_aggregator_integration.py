import unittest
import uuid
import random
import os
from skills.market_stress_risk_aggregator import MarketStressRiskAggregator
from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from skills.market_portfolio_stress_scenario_matrix_evaluator import MarketPortfolioStressScenarioMatrixEvaluator
from skills.db_storage import DBStorage

class TestMarketStressRiskAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = MarketStressRiskAggregator()
        self.monte_carlo = MarketPortfolioStressMonteCarloEngine()
        self.matrix_evaluator = MarketPortfolioStressScenarioMatrixEvaluator()
        self.db = DBStorage()
        self.test_portfolio_id = str(uuid.uuid4())

    def test_stress_risk_aggregation_flow(self):
        # Генерируем случайные параметры для симуляции
        simulation_params = {
            "portfolio_id": self.test_portfolio_id,
            "confidence_level": random.uniform(0.90, 0.99),
            "iterations": random.randint(1000, 5000),
            "shock_factor": random.uniform(0.05, 0.20)
        }

        # 1. Запуск движка Монте-Карло (реальный вызов)
        mc_results = self.monte_carlo.run_simulation(
            portfolio_id=simulation_params["portfolio_id"],
            iterations=simulation_params["iterations"]
        )
        self.assertIn("var_result", mc_results)

        # 2. Запуск оценки матрицы сценариев (реальный вызов)
        matrix_results = self.matrix_evaluator.evaluate(
            portfolio_id=simulation_params["portfolio_id"],
            shock=simulation_params["shock_factor"]
        )
        self.assertIn("scenario_impact", matrix_results)

        # 3. Агрегация через целевой модуль
        aggregated_profile = self.aggregator.aggregate(
            portfolio_id=self.test_portfolio_id,
            mc_data=mc_results,
            matrix_data=matrix_results
        )

        # Проверка структуры и данных
        self.assertEqual(aggregated_profile["portfolio_id"], self.test_portfolio_id)
        self.assertIsInstance(aggregated_profile["risk_score"], float)

        # 4. Сохранение в БД и проверка записи
        save_status = self.db.save_risk_profile(
            profile_id=str(uuid.uuid4()),
            data=aggregated_profile
        )
        self.assertTrue(save_status)

        # 5. Верификация через чтение из БД
        stored_data = self.db.get_latest_profile(self.test_portfolio_id)
        self.assertEqual(stored_data["portfolio_id"], self.test_portfolio_id)
        self.assertGreater(stored_data["timestamp"], 0)

    def tearDown(self):
        # Очистка тестовых данных из хранилища
        self.db.delete_portfolio_records(self.test_portfolio_id)

if __name__ == '__main__':
    unittest.main()