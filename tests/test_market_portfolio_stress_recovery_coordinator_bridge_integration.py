import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_recovery_coordinator_bridge import run_stress_recovery_coordinator_pipeline

class TestMarketPortfolioStressRecoveryCoordinatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(100.0, 2000.0), 2)
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = random.randint(1, 5)
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-DEF{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_recovery_coordinator_bridge_integration(self):
        result = run_stress_recovery_coordinator_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            price=self.price,
            percentage=self.percentage,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            url=self.url
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by the integrated pipeline.")

if __name__ == '__main__':
    unittest.main()