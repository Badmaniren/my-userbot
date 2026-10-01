import unittest
import uuid
import random
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def test_run_simulation_and_stress_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.5), 4)
        drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_value,
                "volatility": volatility,
                "drift": drift
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        simulations = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

        result = engine.run_simulation(portfolio_id, simulations, horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations)

        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)

        stream_res = engine.consume_stream()

        iterations = random.randint(50, 150)
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

        self.assertIsInstance(standalone_result, dict)
        self.assertEqual(standalone_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(standalone_result.get("initial_value"), initial_value)
        self.assertIn("simulation_id", standalone_result)
        self.assertIn("var_95", standalone_result)
        self.assertIn("expected_shortfall", standalone_result)
        self.assertEqual(standalone_result.get("iterations"), iterations)


if __name__ == "__main__":
    unittest.main()