import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer
from skills import market_portfolio_stress_monte_carlo_engine


class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.initial_value = float(random.randint(50000, 500000))
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_monte_carlo_stress_engine_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations = random.randint(100, 500)
        horizon_days = random.randint(10, 30)

        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], str(self.portfolio_id))
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), simulations)
        
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])

        export_res = engine.export_report(self.report_id, loss_limit=15000.0)
        self.assertIsInstance(export_res, dict)
        self.assertIn("report_id", export_res)
        self.assertEqual(export_res["report_id"], self.report_id)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, list, str, bytes)))

    def test_run_monte_carlo_stress_test_function_integration(self):
        iterations = random.randint(100, 300)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": random.randint(5, 15)
        }

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertIn("simulation_id", stress_result)
        self.assertIn("portfolio_id", stress_result)
        self.assertEqual(stress_result["portfolio_id"], str(self.portfolio_id))
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)
        self.assertGreaterEqual(stress_result["expected_shortfall"], stress_result["var_95"])
        self.assertEqual(stress_result["iterations"], iterations)


if __name__ == "__main__":
    unittest.main()