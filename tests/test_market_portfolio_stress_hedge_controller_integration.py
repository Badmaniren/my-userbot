import unittest
import uuid
import random
import os
from skills.db_storage import DBStorage
from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline
from skills.market_portfolio_monitor import MarketPortfolioMonitor
from skills.market_portfolio_stress_hedge_controller import MarketPortfolioStressHedgeController


class TestMarketPortfolioStressHedgeControllerIntegration(unittest.TestCase):

    def setUp(self):
        self.db_storage = DBStorage()
        self.scenario_pipeline = MarketPortfolioStressScenarioPipeline()
        self.execution_pipeline = MarketPortfolioExecutionPipeline()
        self.portfolio_monitor = MarketPortfolioMonitor()

        self.controller = MarketPortfolioStressHedgeController(
            db_storage=self.db_storage,
            scenario_pipeline=self.scenario_pipeline,
            execution_pipeline=self.execution_pipeline,
            portfolio_monitor=self.portfolio_monitor
        )

    def test_evaluate_and_execute_hedge_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        stress_threshold = round(random.uniform(0.01, 0.5), 4)

        result = self.controller.evaluate_and_execute_hedge(portfolio_id, stress_threshold)

        self.assertIn("hedge_order_id", result)
        self.assertIsInstance(result["hedge_order_id"], str)
        self.assertTrue(len(result["hedge_order_id"]) > 0)

    def test_export_last_audit_report_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        expected_path = f"audit_report_{portfolio_id}.txt"

        if os.path.exists(expected_path):
            os.remove(expected_path)

        try:
            report_path = self.controller.export_last_audit_report(portfolio_id)
            self.assertEqual(report_path, expected_path)
            self.assertTrue(os.path.exists(report_path))

            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(portfolio_id, content)
        finally:
            if os.path.exists(expected_path):
                os.remove(expected_path)


if __name__ == "__main__":
    unittest.main()