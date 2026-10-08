import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.random_str = str(uuid.uuid4())[:8]
        self.storage_file = f"test_stress_recovery_{self.random_str}.db"
        self.symbol = f"TEST_{self.random_str.upper()}"
        self.url = f"https://api.telegram.org/bot{random.randint(100000, 999999)}:TEST/sendMessage"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABCdef{random.randint(100, 999)}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = random.randint(1, 5)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_class_execution(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))
        
        result = bridge.execute_recovery_workflow(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("stress_result", result)
        self.assertIn("recovery_result", result)

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
        
        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIsInstance(result, dict)
        self.assertIn("stress", result)
        self.assertIn("recovery", result)

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
        
        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIsInstance(result, dict)
        self.assertIn("stress", result)
        self.assertIn("recovery", result)

if __name__ == "__main__":
    unittest.main()