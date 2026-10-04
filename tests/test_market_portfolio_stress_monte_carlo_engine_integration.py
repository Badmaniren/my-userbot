import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_portfolio_stress_audit_visualizer

class TestMonteCarloStressEngineIntegration(unittest.TestCase):
    def test_integration_monte_carlo_and_visualization(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.4), 2)
        drift = round(random.uniform(-0.05, 0.05), 4)
        horizon_days = random.randint(5, 30)
        iterations = random.randint(100, 500)

        # Подготовка данных в хранилище без использования моков
        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_value,
                "volatility": volatility,
                "drift": drift
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        sim_result = engine.run_simulation(portfolio_id=portfolio_id, simulations=iterations, horizon_days=horizon_days)

        self.assertIn("portfolio_id", sim_result)
        self.assertEqual(sim_result["portfolio_id"], portfolio_id)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertIn("simulation_results", sim_result)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }

        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", standalone_result)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))
        self.assertEqual(standalone_result["portfolio_id"], portfolio_id)
        self.assertEqual(standalone_result["initial_value"], initial_value)
        self.assertIn("var_95", standalone_result)
        self.assertIn("expected_shortfall", standalone_result)

        if hasattr(market_portfolio_stress_audit_visualizer, "visualize_stress_test"):
            vis_result = market_portfolio_stress_audit_visualizer.visualize_stress_test(standalone_result)
            self.assertIsNotNone(vis_result)

if __name__ == "__main__":
    unittest.main()