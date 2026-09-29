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
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_stress_recovery_{self.unique_id}.db"
        self.symbol = f"TICK_{self.unique_id.upper()}"
        self.url = f"https://example.com/webhook/{self.unique_id}"
        self.telegram_token = f"token_{self.unique_id}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = random.randint(1, 5)
        self.price = round(random.uniform(100.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_class_execution(self):
        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        
        result = coordinator.execute_recovery_workflow(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIsInstance(result, dict)
        self.assertIn("stress_result", result)
        self.assertIn("recovery_result", result)
        
        stress_res = result["stress_result"]
        self.assertIsInstance(stress_res, dict)
        if "symbol" in stress_res:
            self.assertEqual(stress_res["symbol"], self.symbol)

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
        
        stress_out = result["stress"]
        self.assertIsInstance(stress_out, dict)

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

        recovery_out = result["recovery"]
        self.assertIsInstance(recovery_out, dict)

if __name__ == "__main__":
    unittest.main()