import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine


class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def test_run_simulation_and_stress_test_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.4), 4)
        drift = round(random.uniform(-0.05, 0.05), 4)
        
        portfolio_payload = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }
        
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[portfolio_id] = portfolio_payload

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        simulations_count = random.randint(100, 500)
        horizon_days = random.randint(5, 30)
        
        simulation_result = engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon_days
        )
        
        self.assertIsInstance(simulation_result, dict)
        self.assertEqual(simulation_result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", simulation_result)
        self.assertIn("var_95", simulation_result)
        self.assertIn("cvar_95", simulation_result)
        self.assertIsInstance(simulation_result["var_95"], float)
        self.assertIsInstance(simulation_result["cvar_95"], float)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }
        iterations = random.randint(100, 500)

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_id", stress_result)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertEqual(stress_result.get("initial_value"), initial_value)
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)
        self.assertEqual(stress_result.get("iterations"), iterations)

    def test_auxiliary_methods_execution(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 15000.0), 2)

        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, str, bytes)))


if __name__ == "__main__":
    unittest.main()