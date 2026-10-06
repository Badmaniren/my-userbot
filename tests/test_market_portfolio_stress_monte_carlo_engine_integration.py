import unittest
import uuid
import random

from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine


class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def test_monte_carlo_simulation_and_stress_test_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = round(random.uniform(50000.0, 150000.0), 2)
        vol = round(random.uniform(0.1, 0.4), 4)
        drift_val = round(random.uniform(-0.05, 0.05), 4)

        if not hasattr(db_storage, "_in_memory_db") or db_storage._in_memory_db is None:
            db_storage._in_memory_db = {}

        db_storage._in_memory_db[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": vol,
            "drift": drift_val
        }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        sim_count = random.randint(50, 200)
        horizon = random.randint(5, 30)

        sim_result = engine.run_simulation(portfolio_id=portfolio_id, simulations=sim_count, horizon_days=horizon)

        self.assertIsInstance(sim_result, dict)
        self.assertEqual(sim_result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", sim_result)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertIsInstance(sim_result["var_95"], float)
        self.assertIsInstance(sim_result["cvar_95"], float)

        scenario_params = {
            "volatility": vol,
            "drift": drift_val,
            "horizon_days": horizon
        }
        iterations = random.randint(50, 200)

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_val,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(stress_result.get("initial_value"), initial_val)
        self.assertIn("simulation_id", stress_result)
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)
        self.assertIsInstance(stress_result["var_95"], float)
        self.assertIsInstance(stress_result["expected_shortfall"], float)

        export_resp = engine.export_report(report_id=portfolio_id, loss_limit=stress_result["var_95"])
        self.assertIsInstance(export_resp, dict)
        self.assertEqual(export_resp.get("report_id"), portfolio_id)

        stream_resp = engine.consume_stream()
        self.assertTrue(stream_resp is None or isinstance(stream_resp, (dict, list, str, bytes)))


if __name__ == "__main__":
    unittest.main()