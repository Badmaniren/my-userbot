import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_testing_dashboard_aggregator_v2 import (
    market_portfolio_stress_testing_dashboard_aggregator_v2
)
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.db_storage import db_storage


class TestMarketPortfolioStressTestingDashboardAggregatorV2Integration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulation_runs = random.randint(100, 1000)
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.output_filepath = f"stress_dashboard_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.output_filepath):
            try:
                os.remove(self.output_filepath)
            except OSError:
                pass

    def test_end_to_end_stress_testing_dashboard_aggregation(self):
        monte_carlo_raw = market_portfolio_stress_monte_carlo_engine(
            portfolio_id=self.portfolio_id,
            simulations=self.simulation_runs,
            confidence=self.confidence_level
        )
        self.assertIsNotNone(monte_carlo_raw, "Монте-Карло движок не должен возвращать None")

        scenario_matrix_result = market_portfolio_stress_scenario_matrix_evaluator(
            portfolio_id=self.portfolio_id,
            monte_carlo_data=monte_carlo_raw
        )
        self.assertIsNotNone(scenario_matrix_result, "Матрица сценариев не должна возвращать None")

        stress_report = market_portfolio_stress_reporter(
            portfolio_id=self.portfolio_id,
            matrix_data=scenario_matrix_result,
            output_path=self.output_filepath
        )
        self.assertIsNotNone(stress_report, "Стресс-репортер не должен возвращать None")

        dashboard_summary = market_portfolio_stress_testing_dashboard_aggregator_v2(
            portfolio_id=self.portfolio_id,
            report_data=stress_report,
            storage_handler=db_storage
        )

        self.assertIsInstance(dashboard_summary, dict, "Агрегатор должен возвращать словарь с метриками")
        self.assertIn("dashboard_id", dashboard_summary)
        self.assertEqual(dashboard_summary.get("portfolio_id"), self.portfolio_id)

        self.assertTrue(
            os.path.exists(self.output_filepath),
            f"Интеграционный процесс должен сформировать файл отчета: {self.output_filepath}"
        )


if __name__ == "__main__":
    unittest.main()