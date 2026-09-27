import unittest
import uuid
import random
from skills.market_portfolio_macro_indicator import market_portfolio_macro_indicator

class TestMarketPortfolioMacroIndicatorIntegration(unittest.TestCase):
    def test_process_indicators_integration(self):
        indicator_module = market_portfolio_macro_indicator()

        unique_request_id = str(uuid.uuid4())
        random_inflation = round(random.uniform(0.5, 10.0), 2)
        random_gdp = round(random.uniform(-3.0, 6.0), 2)

        raw_payload = {
            "inflation": random_inflation,
            "gdp": random_gdp
        }

        result = indicator_module.process_indicators(raw_payload, unique_request_id)

        self.assertIsInstance(result, dict)
        self.assertIn("correlation_id", result)
        self.assertIn("metrics", result)

        self.assertEqual(result["correlation_id"], unique_request_id)

        metrics = result["metrics"]
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics.get("inflation_rate"), random_inflation)
        self.assertEqual(metrics.get("gdp_growth"), random_gdp)

if __name__ == "__main__":
    unittest.main()