import unittest
import os
import uuid
import random
from skills.market_portfolio_integration_validation_bridge import (
    MarketPortfolioIntegrationValidationBridge
)
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioIntegrationValidationBridge(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.bridge = MarketPortfolioIntegrationValidationBridge(db_storage=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_end_to_end_validation_pipeline(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        simulations = random.randint(100, 1000)
        horizon_days = random.randint(1, 30)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        
        url = f"https://api.test-market-data.org/v1/feed/{uuid.uuid4().hex}"
        symbol = f"TICKER_{random.choice(['AAPL', 'BTC', 'ETH', 'SPY'])}"
        shifts = [random.randint(-10, 10), random.randint(-5, 5)]
        telegram_token = f"TOKEN_{uuid.uuid4().hex}"
        chat_id = str(random.randint(100000, 999999))

        result = self.bridge.run_validation_and_integration_pipeline(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            portfolio_value=portfolio_value,
            url=url,
            symbol=symbol,
            shifts=shifts,
            telegram_token=telegram_token,
            chat_id=chat_id
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn("validation_status", result)
        self.assertTrue(result["validation_status"])
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("scenario_code"), scenario_code)

if __name__ == '__main__':
    unittest.main()