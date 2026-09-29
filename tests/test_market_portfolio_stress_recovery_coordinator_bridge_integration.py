import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestMarketPortfolioStressRecoveryCoordinatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_stress_recovery_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test-webhook-{uuid.uuid4()}.local/hook"
        self.telegram_token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_recovery_coordinator_bridge_class(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertEqual(bridge.storage_file, self.storage_file)
        
        result = bridge.execute_recovery_workflow(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )
        
        self.assertIn("stress_result", result)
        self.assertIn("recovery_result", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_run_stress_recovery_coordinator_function(self):
        result = run_stress_recovery_coordinator(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIn("stress", result)
        self.assertIn("recovery", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_run_stress_recovery_coordinator_pipeline_function(self):
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

        self.assertIn("stress", result)
        self.assertIn("recovery", result)
        
        stress_data = result["stress"]
        self.assertIsInstance(stress_data, dict)
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()