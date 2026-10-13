import unittest
import os
import json
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
        self.symbol = f"TICKER_{self.random_str}"
        self.url = f"https://api.test-webhook-{self.random_str}.com/hook"
        self.telegram_token = f"TOKEN_{self.random_str}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(5.0, 35.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_class_bridge_execution(self):
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

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol]["percentage"], self.percentage)
        self.assertEqual(data[self.symbol]["shifts"], self.shifts)

    def test_coordinator_function_execution(self):
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

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol]["status"], "coordinator_run")

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

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol]["price"], self.price)
        self.assertEqual(data[self.symbol]["status"], "pipeline_run")

if __name__ == "__main__":
    unittest.main()