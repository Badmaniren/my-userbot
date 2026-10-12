import unittest
import uuid
import random
from skills.market_portfolio_stress_resilience_analyzer import (
    MarketPortfolioStressResilienceAnalyzer,
    market_portfolio_stress_resilience_analyzer
)
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.db_storage import db_storage

class TestMarketPortfolioStressResilienceAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer_class_instance = MarketPortfolioStressResilienceAnalyzer(
            db_storage=db_storage,
            market_portfolio_scenario_simulator=market_portfolio_scenario_simulator,
            market_portfolio_monitor=market_portfolio_monitor
        )

    def test_evaluate_resilience_integration(self):
        random_portfolio_id = str(uuid.uuid4())
        random_scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"

        result = self.analyzer_class_instance.evaluate_resilience(
            portfolio_id=random_portfolio_id,
            scenario_id=random_scenario_id
        )

        self.assertIn("resilience_score", result)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["scenario_id"], random_scenario_id)
        self.assertIn("health_status", result)
        self.assertIn("scenario_metrics", result)
        self.assertIsInstance(result["resilience_score"], float)

    def test_function_wrapper_integration(self):
        random_portfolio_id = str(uuid.uuid4())
        simulated_val = round(random.uniform(100.0, 50000.0), 2)
        corr_factor = round(random.uniform(0.1, 1.0), 2)

        payload = {
            "portfolio_id": random_portfolio_id,
            "simulation_data": {
                "simulated_value": simulated_val
            },
            "subsystem_health": {
                "health_status": "GREEN"
            },
            "correlation_factor": corr_factor
        }

        func_result = market_portfolio_stress_resilience_analyzer(payload)

        self.assertEqual(func_result["portfolio_id"], random_portfolio_id)
        self.assertEqual(func_result["status"], "ANALYZED")
        self.assertIsInstance(func_result["resilience_score"], float)

        expected_score = round(80.0 + (simulated_val * 0.00001) * corr_factor, 2)
        self.assertEqual(func_result["resilience_score"], expected_score)

if __name__ == "__main__":
    unittest.main()