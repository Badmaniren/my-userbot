import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_risk_aggregator import market_portfolio_stress_risk_aggregator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.db_storage import db_storage

class TestMarketPortfolioStressRiskAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.session_id = str(uuid.uuid4())
        self.risk_threshold = random.uniform(0.01, 0.05)

    def test_aggregation_pipeline_flow(self):
        # 1. Инициализация движка Монте-Карло для генерации сырых данных
        mc_engine = market_portfolio_stress_monte_carlo_engine()
        raw_simulation_data = mc_engine.run_simulation(
            portfolio_id=self.portfolio_id,
            iterations=1000,
            confidence_level=0.95
        )

        # 2. Оценка сценариев через матричный эвалюатор
        matrix_evaluator = market_portfolio_stress_scenario_matrix_evaluator()
        scenario_results = matrix_evaluator.evaluate(
            simulation_data=raw_simulation_data,
            stress_factors={'volatility_spike': random.uniform(1.5, 3.0)}
        )

        # 3. Агрегация через целевой модуль (без моков)
        aggregator = market_portfolio_stress_risk_aggregator()
        aggregation_result = aggregator.aggregate(
            session_id=self.session_id,
            portfolio_id=self.portfolio_id,
            monte_carlo_output=raw_simulation_data,
            scenario_matrix=scenario_results
        )

        # Проверка возвращаемого ID
        self.assertIsNotNone(aggregation_result.get("aggregation_id"))
        self.assertEqual(aggregation_result.get("portfolio_id"), self.portfolio_id)

        # 4. Проверка сохранения в реальное хранилище (db_storage)
        db = db_storage()
        stored_record = db.get_record(
            table="stress_risk_aggregates",
            key=aggregation_result["aggregation_id"]
        )

        self.assertIsNotNone(stored_record, "Данные не были записаны в db_storage")
        self.assertIn("var_value", stored_record)
        self.assertIn("cvar_value", stored_record)

        # 5. Валидация целостности данных
        self.assertTrue(
            stored_record["var_value"] < stored_record["cvar_value"],
            "VaR должен быть меньше или равен CVaR"
        )

    def test_persistence_integrity(self):
        # Проверка создания артефакта (например, JSON-отчета для визуализатора)
        aggregator = market_portfolio_stress_risk_aggregator()
        test_file_path = f"stress_report_{self.session_id}.json"

        aggregator.export_to_file(
            session_id=self.session_id,
            path=test_file_path
        )

        self.assertTrue(os.path.exists(test_file_path), "Файл отчета не был создан на диске")

        # Очистка
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == '__main__':
    unittest.main()