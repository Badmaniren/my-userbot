import unittest
import os
import uuid
import random
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel, run_autonomous_sentinel

class TestAutonomousSentinelIntegration(unittest.TestCase):
    def setUp(self):
        self.test_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_sentinel_storage_{self.test_suffix}.json"
        self.symbol = f"TST_{uuid.uuid4().hex[:4].upper()}"
        self.url = f"https://example.com/api/v1/market/{uuid.uuid4().hex}"
        self.telegram_token = f"123456:ABC-DEF{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.threshold = round(random.uniform(1.0, 10.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_autonomous_sentinel_integration(self):
        result = run_autonomous_sentinel(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            threshold=self.threshold
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("forecast", result)
        self.assertIn(result["status"], ["triggered", "stable"])
        
        sentinel = AutonomousSentinel(
            storage_file=self.storage_file,
            threshold=self.threshold
        )
        surveillance_result = sentinel.run_surveillance(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        
        self.assertIsInstance(surveillance_result, dict)
        self.assertIn("status", surveillance_result)

if __name__ == "__main__":
    unittest.main()