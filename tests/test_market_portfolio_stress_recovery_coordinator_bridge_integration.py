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
        self.storage_file = f"test_stress_recovery_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.mock-endpoint-{uuid.uuid4().hex[:8]}.test/webhook"
        self.telegram_token = f"token_{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(100000000, 999999999))
        self.percentage = round(random.uniform(5.0, 35.0), 2)
        self.shifts = random.randint(3, 10)
        self.price = round(random.uniform(100.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_class_bridge_execution(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created upon initialization.")

        result = bridge.execute_recovery_workflow(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict, "Execution result must be a dictionary.")
        self.assertIn("stress_result", result)
        self.assertIn("recovery_result", result)
        
        stress_res = result["stress_result"]
        self.assertIsInstance(stress_res, dict)
        self.assertIn("status", stress_res)

    def test_functional_coordinator_execution(self):
        result = run_stress_recovery_coordinator(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertIn("stress", result)
        self.assertIn("recovery", result)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must exist after functional run.")

    def test_coordinator_pipeline_execution(self):
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

        self.assertIsInstance(result, dict)
        self.assertIn("stress", result)
        self.assertIn("recovery", result)
        
        recovery_data = result["recovery"]
        self.assertIsInstance(recovery_data, dict)
        self.assertTrue(os.path.exists(self.storage_file), "Pipeline must initialize and persist storage.")

if __name__ == '__main__':
    unittest.main()