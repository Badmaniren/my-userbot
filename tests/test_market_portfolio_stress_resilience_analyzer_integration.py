import unittest
import uuid
import random
from skills.market_portfolio_stress_resilience_analyzer import market_portfolio_stress_resilience_analyzer
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter


class TestMarketPortfolioStressResilienceAnalyzerIntegration(unittest.TestCase):

    def test_market_portfolio_stress_resilience_flow(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        random_db_ref = f"db_ref_{uuid.uuid4().hex[:8]}"
        random_threshold = round(random.uniform(1.0, 50.0), 2)

        payload = {
            "portfolio_id": random_portfolio_id,
            "db_reference": random_db_ref,
            "threshold": random_threshold
        }

        simulation_metrics = market_portfolio_scenario_simulator.run_stress_test(
            portfolio_id=random_portfolio_id,
            intensity=random_threshold,
            scenario="integration_shock_scenario"
        )
        self.assertIsNotNone(simulation_metrics)

        market_portfolio_stress_reporter.generate_report(simulation_metrics)
        db_storage.save_stress_results(simulation_metrics)

        result = market_portfolio_stress_resilience_analyzer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("db_reference"), random_db_ref)
        self.assertEqual(result.get("status"), "COMPLETED")
        
        expected_score = round(100.0 - abs(float(random_threshold)), 2)
        self.assertEqual(result.get("resilience_score"), expected_score)


if __name__ == "__main__":
    unittest.main()