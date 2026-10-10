import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_monte_carlo_engine


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_and_monte_carlo_stress_test(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = round(random.uniform(50000.0, 500000.0), 2)
        vol = round(random.uniform(0.1, 0.5), 4)
        drift = round(random.uniform(-0.05, 0.05), 4)
        
        simulations_count = random.randint(100, 500)
        horizon = random.randint(5, 30)

        if not hasattr(db_storage, "_in_memory_db") or db_storage._in_memory_db is None:
            db_storage._in_memory_db = {}
        
        db_storage._in_memory_db[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": vol,
            "drift": drift
        }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        sim_result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon)

        self.assertIsInstance(sim_result, dict)
        self.assertEqual(sim_result["portfolio_id"], portfolio_id)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertGreaterEqual(sim_result["cvar_95"], sim_result["var_95"])

        scenario_params = {
            "volatility": vol,
            "drift": drift,
            "horizon_days": horizon
        }
        iterations = random.randint(100, 500)

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_val,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["portfolio_id"], portfolio_id)
        self.assertEqual(stress_result["initial_value"], initial_val)
        self.assertIn("simulation_id", stress_result)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertIn("expected_shortfall", stress_result)
        self.assertGreaterEqual(stress_result["expected_shortfall"], stress_result["var_95"])

    def test_anomaly_detector_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        adjustment = engine._get_anomaly_adjustment()
        self.assertIsInstance(adjustment, float)
        self.assertGreater(adjustment, 0.0)


if __name__ == "__main__":
    unittest.main()