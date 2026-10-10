import unittest
import uuid
import random
import os
from skills.market_portfolio_integration_validation_bridge import MarketPortfolioIntegrationValidationBridge
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioIntegrationValidationBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_bridge_{uuid.uuid4().hex}.sqlite"
        self.bridge = MarketPortfolioIntegrationValidationBridge(db_storage=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_run_end_to_end_validation_pipeline_real_execution(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_scenario = f"scen_{uuid.uuid4().hex[:6]}"
        rand_symbol = f"SYM{random.randint(100, 999)}"
        rand_val = round(random.uniform(10000.0, 500000.0), 2)
        rand_sims = random.randint(100, 1000)
        rand_horizon = random.randint(1, 30)
        rand_conf = round(random.uniform(0.90, 0.99), 2)
        rand_shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        
        result = self.bridge.run_end_to_end_validation_pipeline(
            portfolio_id=rand_portfolio_id,
            scenario_code=rand_scenario,
            url=f"http://127.0.0.1:{random.randint(8000, 9999)}/api",
            symbol=rand_symbol,
            shifts=rand_shifts,
            telegram_token=f"token_{uuid.uuid4().hex[:6]}",
            chat_id=str(random.randint(100000, 999999)),
            simulations=rand_sims,
            horizon_days=rand_horizon,
            confidence_level=rand_conf,
            port_value=rand_val,
            scenario_params={"volatility_shock": random.uniform(0.1, 0.5)},
            iterations=random.randint(5, 20)
        )

        self.assertIn("validation_id", result)
        self.assertIn("var_report", result)
        self.assertIn("integration_report", result)
        self.assertEqual(result["overall_status"], "PASSED")
        self.assertIsInstance(result["validation_id"], str)
        self.assertTrue(len(result["validation_id"]) > 0)

    def test_run_stress_validation_bridge_execution(self):
        rand_portfolio_id = f"stress_port_{uuid.uuid4().hex[:8]}"
        rand_val = round(random.uniform(50000.0, 1000000.0), 2)
        rand_conf = round(random.uniform(0.95, 0.99), 4)
        rand_horizon = random.randint(5, 60)

        stress_result = self.bridge.run_stress_validation_bridge(
            portfolio_id=rand_portfolio_id,
            portfolio_value=rand_val,
            scenario_params={"shock_level": random.uniform(0.2, 0.8)},
            confidence_level=rand_conf,
            horizon_days=rand_horizon,
            iterations=random.randint(10, 30)
        )

        self.assertIsInstance(stress_result, dict)

    def test_stream_validation_audit_export_execution(self):
        stream_payload = {
            "stream_id": uuid.uuid4().hex,
            "timestamp": random.randint(1600000000, 1700000000),
            "metric": random.random()
        }

        export_res = self.bridge.stream_validation_audit_export(stream_payload)
        self.assertIsInstance(export_res, dict)

    def test_run_validation_and_integration_pipeline_fallback(self):
        rand_portfolio_id = f"pipe_{uuid.uuid4().hex[:8]}"
        rand_scenario = f"code_{uuid.uuid4().hex[:6]}"
        rand_val = round(random.uniform(1000.0, 50000.0), 2)

        pipeline_res = self.bridge.run_validation_and_integration_pipeline(
            portfolio_id=rand_portfolio_id,
            scenario_code=rand_scenario,
            simulations=random.randint(50, 200),
            horizon_days=random.randint(1, 10),
            confidence_level=0.95,
            portfolio_value=rand_val,
            url=f"http://localhost:{random.randint(1000, 5000)}/hook",
            symbol=f"TICK_{random.randint(10, 99)}",
            shifts=[random.random()],
            telegram_token=f"bot{random.randint(1000,9999)}",
            chat_id=str(random.randint(100, 999))
        )

        self.assertTrue(pipeline_res["validation_status"])
        self.assertEqual(pipeline_res["portfolio_id"], rand_portfolio_id)
        self.assertEqual(pipeline_res["scenario_code"], rand_scenario)
        self.assertIn("var_report", pipeline_res)

if __name__ == "__main__":
    unittest.main()