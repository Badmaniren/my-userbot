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
        self.symbol = f"TEST_{random.choice(['BTC', 'ETH', 'SOL', 'AAPL'])}_{self.unique_id}"
        self.url = f"https://api.fake-webhook-{self.unique_id}.local/endpoint"
        self.telegram_token = f"fake_token_{self.unique_id}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(0.01, 0.25), 4)
        self.shifts = random.randint(3, 10)
        self.price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_class_bridge_execution_flow(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file should be created upon bridge initialization.")

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

        stress_res = result["stress_result"]
        self.assertIsInstance(stress_res, dict)

        # Verify dynamic symbol representation inside results to avoid hardcoded stubs
        if "symbol" in stress_res:
            self.assertEqual(stress_res["symbol"], self.symbol)

    def test_functional_coordinator_runner(self):
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
        self.assertTrue(os.path.exists(self.storage_file))

    def test_pipeline_coordinator_runner(self):
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

        stress_data = result["stress"]
        self.assertIsInstance(stress_data, dict)
        if "symbol" in stress_data:
            self.assertEqual(stress_data["symbol"], self.symbol)

if __name__ == '__main__':
    unittest.main()