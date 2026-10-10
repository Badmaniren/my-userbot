import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage

class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_run_simulation_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations = random.randint(50, 200)
        horizon_days = random.randint(10, 30)

        result = engine.run_simulation(self.portfolio_id, simulations, horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])
        self.assertEqual(len(result["simulation_results"]), simulations)

    def test_run_monte_carlo_stress_test_integration(self):
        iterations = random.randint(50, 200)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": random.randint(5, 15)
        }

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], self.initial_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertGreaterEqual(result["expected_shortfall"], result["var_95"])

    def test_export_report_and_consume_stream(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)

        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))


if __name__ == "__main__":
    unittest.main()