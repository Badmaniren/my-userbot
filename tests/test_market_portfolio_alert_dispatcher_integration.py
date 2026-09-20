import unittest
import os
import uuid
import random
import tempfile
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts


class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4()}.json")
        
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"http://example.com/api/{uuid.uuid4()}"
        self.telegram_token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dispatch_portfolio_alerts_integration(self):
        result = dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.storage_file))


if __name__ == "__main__":
    unittest.main()