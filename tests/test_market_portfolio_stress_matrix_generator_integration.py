import unittest
import uuid
import random

from skills import market_portfolio_stress_matrix_generator
from skills import db_storage
from skills import market_portfolio_scenario_simulator

class TestMarketPortfolioStressMatrixGeneratorIntegration(unittest.TestCase):

    def test_generate_stress_matrix_integration_string_scenario(self):
        portfolio_id = f"test_port_{uuid.uuid4().hex[:8]}"
        scenario_code = f"CRASH_{random.randint(100, 999)}"

        test_portfolio_data = {
            "portfolio_id": portfolio_id,
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "value": random.uniform(1000, 50000)},
                {"ticker": "GOOGL", "weight": 0.5, "value": random.uniform(1000, 50000)}
            ]
        }

        try:
            if hasattr(db_storage, "save_portfolio"):
                db_storage.save_portfolio(portfolio_id, test_portfolio_data)
            elif hasattr(db_storage, "store_portfolio"):
                db_storage.store_portfolio(portfolio_id, test_portfolio_data)
            else:
                if not hasattr(db_storage, "_STORAGE"):
                    db_storage._STORAGE = {}
                db_storage._STORAGE[portfolio_id] = test_portfolio_data
        except Exception:
            if not hasattr(db_storage, "_STORAGE"):
                db_storage._STORAGE = {}
            db_storage._STORAGE[portfolio_id] = test_portfolio_data

        original_simulate = getattr(market_portfolio_scenario_simulator, "simulate", None)
        random_multiplier = round(random.uniform(0.1, 0.9), 4)

        def mock_simulate(data, sc):
            return {"multiplier": random_multiplier, "scenario": sc}

        market_portfolio_scenario_simulator.simulate = mock_simulate

        try:
            result = market_portfolio_stress_matrix_generator.generate_stress_matrix(
                portfolio_id=portfolio_id,
                simulation_data=scenario_code
            )

            self.assertIsInstance(result, dict)
            self.assertIn("matrix_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario"], scenario_code)
            self.assertEqual(result["result"], random_multiplier)
            self.assertTrue(len(result["matrix_id"]) > 0)
        finally:
            if original_simulate is not None:
                market_portfolio_scenario_simulator.simulate = original_simulate

    def test_generate_stress_matrix_integration_default_branch(self):
        portfolio_id = f"test_port_{uuid.uuid4().hex[:8]}"
        sim_data = {"simulation_run_id": uuid.uuid4().hex, "metric": random.randint(1, 100)}
        mc_data = {"monte_carlo_var": random.uniform(0.01, 0.5)}

        result = market_portfolio_stress_matrix_generator.generate_stress_matrix(
            portfolio_id=portfolio_id,
            simulation_data=sim_data,
            monte_carlo_data=mc_data
        )

        self.assertIsInstance(result, dict)
        self.assertIn("matrix_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["simulation_data"], sim_data)
        self.assertEqual(result["monte_carlo_data"], mc_data)
        self.assertEqual(result["matrix_data"]["status"], "GENERATED")
        self.assertTrue(result["persisted"])

if __name__ == "__main__":
    unittest.main()