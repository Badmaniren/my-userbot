import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_recovery_hub import (
    StressRecoveryHub,
    run_stress_recovery_pipeline,
    execute_recovery_strategy,
    run_recovery_pipeline,
    execute_recovery
)


class TestStressRecoveryHubIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = "http://localhost:8000"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(1.0, 20.0), 2)
        self.shifts = random.randint(1, 5)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_comprehensive_pipeline_integration(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        result = hub.run_comprehensive_pipeline(
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertIn("monitor", result)
        self.assertIn("stress", result)

    def test_generate_recovery_recommendation_integration(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        threshold = round(random.uniform(0.01, 0.5), 4)
        rec = hub.generate_recovery_recommendation(threshold=threshold)

        self.assertIsInstance(rec, dict)
        self.assertEqual(rec.get("action"), "rebalance_portfolio")
        self.assertEqual(rec.get("symbol"), self.symbol)
        self.assertEqual(rec.get("threshold"), threshold)
        self.assertIn("data", rec)

    def test_convenience_functions_integration(self):
        res1 = run_stress_recovery_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            percentage=self.percentage,
            shifts=self.shifts
        )
        self.assertIsInstance(res1, dict)
        self.assertIn("monitor", res1)
        self.assertIn("stress", res1)

        res2 = run_recovery_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertIsInstance(res2, dict)

        res3 = execute_recovery(
            storage_file=self.storage_file,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertIsInstance(res3, dict)

    def test_execute_recovery_strategy_integration(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        strategy_result = execute_recovery_strategy(hub)
        self.assertIsInstance(strategy_result, dict)
        self.assertTrue(strategy_result.get("stream_dump_processed"))


if __name__ == "__main__":
    unittest.main()