import unittest
import uuid
import random
from skills.market_portfolio_var_web_publisher import market_portfolio_var_web_publisher, MarketPortfolioVarWebPublisher, VarPublisherException
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway
from skills.db_storage import db_storage

class TestMarketPortfolioVarWebPublisherIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.webhook_url = f"https://httpbin.org/post"
        self.api_token = f"token_{uuid.uuid4().hex}"
        self.var_data = {
            "var_95": round(random.uniform(1000.0, 50000.0), 2),
            "var_99": round(random.uniform(5000.0, 100000.0), 2),
            "confidence_level": random.choice([0.95, 0.99])
        }

    def test_real_integration_publisher_workflow(self):
        try:
            result = market_portfolio_var_web_publisher(
                portfolio_id=self.portfolio_id,
                webhook_url=self.webhook_url,
                var_data=self.var_data,
                api_token=self.api_token
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(result.get("target_webhook"), self.webhook_url)
            self.assertIn("status", result)
            self.assertIn("published_id", result)

        except VarPublisherException as e:
            self.fail(f"Integration publishing failed with exception: {e}")

    def publisher_direct_class_verification(self):
        publisher = MarketPortfolioVarWebPublisher(
            webhook_url=self.webhook_url,
            api_token=self.api_token
        )
        headers = publisher._get_headers()
        self.assertEqual(headers.get("Authorization"), f"Bearer {self.api_token}")

if __name__ == "__main__":
    unittest.main()