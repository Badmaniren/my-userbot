import unittest
import uuid
import random
import logging
from skills.market_portfolio_integration_validation_bridge import MarketPortfolioIntegrationValidationBridge

logging.basicConfig(level=logging.INFO)

class TestMarketPortfolioIntegrationValidationBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.db_name = f"test_bridge_{uuid.uuid4().hex}.sqlite"
        self.bridge = MarketPortfolioIntegrationValidationBridge(db_storage=self.db_name)

    def test_end_to_end_validation_pipeline_real_execution(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        symbol = random.choice(["AAPL", "GOOGL", "TSLA", "MSFT", "BTC-USD"])
        port_value = round(random.uniform(10000.0, 1000000.0), 2)
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 30)
        confidence_level = round(random.uniform(0.90, 0.99), 2)
        iterations = random.randint(5, 20)
        shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        
        url = f"https://api.test-market-{uuid.uuid4().hex[:6]}.org/feed"
        telegram_token = f"token_{uuid.uuid4().hex[:10]}"
        chat_id = str(random.randint(100000, 999999))
        
        scenario_params = {"shock_factor": round(random.uniform(0.05, 0.5), 2)}

        result = self.bridge.run_end_to_end_validation_pipeline(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            url=url,
            symbol=symbol,
            shifts=shifts,
            telegram_token=telegram_token,
            chat_id=chat_id,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            port_value=port_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("overall_status"), "PASSED")
        self.assertIn("validation_id", result)
        self.assertIn("var_report", result)
        self.assertIn("integration_report", result)

    def test_run_stress_validation_bridge_execution(self):
        portfolio_id = f"port_stress_{uuid.uuid4().hex[:8]}"
        port_value = round(random.uniform(50000.0, 500000.0), 2)
        confidence_level = 0.95
        horizon_days = 10
        iterations = 10
        scenario_params = {"drop": -0.2}

        stress_res = self.bridge.run_stress_validation_bridge(
            portfolio_id=portfolio_id,
            portfolio_value=port_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

        self.assertIsInstance(stress_res, dict)

    def test_run_validation_and_integration_pipeline_error_handling(self):
        portfolio_id = f"err_port_{uuid.uuid4().hex[:8]}"
        scenario_code = f"err_scen_{uuid.uuid4().hex[:8]}"
        url = f"https://faulty-api-{uuid.uuid4().hex[:6]}.net/data"
        symbol = "INVALID_SYM"
        shifts = [0.01, -0.02]
        telegram_token = "bad_token"
        chat_id = "000000"

        res = self.bridge.run_validation_and_integration_pipeline(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=10,
            horizon_days=5,
            confidence_level=0.99,
            portfolio_value=1000.0,
            url=url,
            symbol=symbol,
            shifts=shifts,
            telegram_token=telegram_token,
            chat_id=chat_id
        )

        self.assertIsInstance(res, dict)
        self.assertTrue(res.get("validation_status"))
        self.assertEqual(res.get("portfolio_id"), portfolio_id)
        self.assertEqual(res.get("scenario_code"), scenario_code)
        self.assertIn("var_report", res)

if __name__ == "__main__":
    unittest.main()