import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import os

from skills.market_portfolio_strategy_backtest_sync import (
    PortfolioStrategyBacktestSync,
    run_strategy_backtest_sync
)


class TestPortfolioStrategyBacktestSync(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.filepath = f"{uuid.uuid4().hex}.bin"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except OSError:
                pass

    def test_initialization(self):
        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        self.assertEqual(syncer.storage_file, self.storage_file)
        self.assertIsNotNone(syncer.optimizer)
        self.assertIsNotNone(syncer.backtester)

    @patch("skills.market_portfolio_strategy_backtest_sync.PortfolioStrategyOptimizer")
    @patch("skills.market_portfolio_strategy_backtest_sync.MarketPortfolioBacktester")
    def test_sync_strategy_params(self, mock_backtester_cls, mock_optimizer_cls):
        mock_optimizer = mock_optimizer_cls.return_value
        mock_backtester = mock_backtester_cls.return_value

        opt_res = {"backtest": {"opt": 1}, "simulation": {"sim": 2}}
        backtest_res = {"status": "completed"}
        resilience_res = {"stress_data": {}, "drawdown_checked": 0.05}

        mock_optimizer.optimize_strategy.return_value = opt_res
        mock_backtester.run_backtest.return_value = backtest_res
        mock_optimizer.evaluate_resilience.return_value = resilience_res

        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        pct = random.uniform(1.0, 10.0)

        result = syncer.sync_strategy_params(self.symbol, shifts=shifts, percentage=pct)

        self.assertEqual(result["status"], "synchronized")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["optimization"], opt_res)
        self.assertEqual(result["backtest"], backtest_res)
        self.assertEqual(result["resilience"], resilience_res)
        self.assertEqual(result["synchronized_params"]["optimal_shifts"], shifts)

    @patch("skills.market_portfolio_strategy_backtest_sync.PortfolioStrategyOptimizer")
    @patch("skills.market_portfolio_strategy_backtest_sync.MarketPortfolioBacktester")
    def test_evaluate_and_sync(self, mock_backtester_cls, mock_optimizer_cls):
        mock_optimizer = mock_optimizer_cls.return_value
        mock_backtester = mock_backtester_cls.return_value

        resilience_res = {"stress_data": {"level": "low"}, "drawdown_checked": 0.02}
        mock_optimizer.evaluate_resilience.return_value = resilience_res
        mock_optimizer.optimize_strategy.return_value = {}
        mock_backtester.run_backtest.return_value = {}

        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        shifts = [random.randint(1, 3)]
        pct = random.uniform(0.5, 5.0)

        res = syncer.evaluate_and_sync(self.symbol, shifts=shifts, percentage=pct)

        self.assertEqual(res["sync_status"], "synchronized")
        self.assertEqual(res["resilience"], resilience_res)
        self.assertIn("sync_details", res)

    def test_export_sync_dump(self):
        sample_bytes = uuid.uuid4().bytes
        with open(self.filepath, "wb") as f:
            f.write(sample_bytes)

        syncer = PortfolioStrategyBacktestSync(self.storage_file)
        data = syncer.export_sync_dump(self.filepath)
        self.assertEqual(data, sample_bytes)

    @patch("skills.market_portfolio_strategy_backtest_sync.PortfolioStrategyBacktestSync.sync_strategy_params")
    def test_run_strategy_backtest_sync_function(self, mock_sync):
        mock_sync.return_value = {"status": "synchronized"}
        shifts = [1, 2, 3]
        pct = 2.5

        res = run_strategy_backtest_sync(self.storage_file, self.symbol, shifts=shifts, percentage=pct)

        self.assertEqual(res, {"status": "synchronized"})
        mock_sync.assert_called_once_with(self.symbol, shifts, pct)


if __name__ == "__main__":
    unittest.main()
