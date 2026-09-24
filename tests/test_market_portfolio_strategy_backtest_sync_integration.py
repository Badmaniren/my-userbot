import unittest
import os
import json
import uuid
import random
import string

from skills.market_portfolio_strategy_backtest_sync import (
    PortfolioStrategyBacktestSync,
    run_strategy_backtest_sync
)


class TestPortfolioStrategyBacktestSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_sync_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"

        # Populate storage file with mock historical price data
        self.sample_data = {
            self.symbol: [
                {"price": round(random.uniform(100.0, 150.0), 2), "timestamp": 1},
                {"price": round(random.uniform(120.0, 180.0), 2), "timestamp": 2},
                {"price": round(random.uniform(110.0, 160.0), 2), "timestamp": 3},
                {"price": round(random.uniform(130.0, 190.0), 2), "timestamp": 4}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_data, f)

        self.bin_file = f"test_dump_{self.random_suffix}.bin"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.bin_file):
            try:
                os.remove(self.bin_file)
            except OSError:
                pass

    def test_sync_strategy_params_integration(self):
        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        pct = random.uniform(2.0, 8.0)

        result = syncer.sync_strategy_params(self.symbol, shifts=shifts, percentage=pct)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "synchronized")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("optimization", result)
        self.assertIn("backtest", result)
        self.assertIn("resilience", result)
        self.assertIn("synchronized_params", result)

    def test_evaluate_and_sync_integration(self):
        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        shifts = [1, 2]
        pct = 5.0

        res = syncer.evaluate_and_sync(self.symbol, shifts=shifts, percentage=pct)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("sync_status"), "synchronized")
        self.assertIn("resilience", res)
        self.assertIn("sync_details", res)

    def test_export_sync_dump_integration(self):
        test_payload = uuid.uuid4().bytes
        with open(self.bin_file, "wb") as f:
            f.write(test_payload)

        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        read_data = syncer.export_sync_dump(self.bin_file)

        self.assertEqual(read_data, test_payload)

    def test_run_strategy_backtest_sync_integration(self):
        shifts = [random.randint(1, 3), random.randint(4, 6)]
        pct = random.uniform(1.0, 5.0)

        result = run_strategy_backtest_sync(self.storage_file, self.symbol, shifts=shifts, percentage=pct)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "synchronized")
        self.assertEqual(result.get("symbol"), self.symbol)


if __name__ == "__main__":
    unittest.main()
