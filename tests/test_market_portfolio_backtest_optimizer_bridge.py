import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import uuid
import random
import json

from skills.market_portfolio_backtest_optimizer_bridge import PortfolioBacktestOptimizerBridge


class TestPortfolioBacktestOptimizerBridge(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

        data = {
            str(uuid.uuid4().hex[:6]): [
                {"price": round(random.uniform(10.0, 100.0), 2), "timestamp": random.randint(1000, 5000)}
                for _ in range(5)
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        self.symbol = list(data.keys())[0]
        self.bridge = PortfolioBacktestOptimizerBridge(self.storage_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_bridge_pipeline_success(self):
        random_shifts = random.randint(1, 5)
        random_percentage = round(random.uniform(0.01, 0.5), 2)

        mock_optimizer_result = {
            str(uuid.uuid4().hex): round(random.uniform(0.1, 1.0), 2),
            "optimal_weight": round(random.uniform(0.0, 1.0), 2)
        }
        mock_equity_curve = [
            round(random.uniform(100.0, 200.0), 2),
            round(random.uniform(150.0, 250.0), 2)
        ]
        mock_max_drawdown = round(random.uniform(0.0, 0.5), 4)
        mock_summary = {
            str(uuid.uuid4().hex): str(uuid.uuid4().hex),
            "total_return": round(random.uniform(-0.2, 0.5), 2)
        }

        with patch.object(self.bridge.optimizer, "optimize_strategy", return_value=mock_optimizer_result) as mock_opt, \
             patch.object(self.bridge.backtester, "run_backtest", return_value=mock_equity_curve) as mock_bt, \
             patch.object(self.bridge.backtester, "calculate_maximum_drawdown", return_value=mock_max_drawdown) as mock_mdd, \
             patch.object(self.bridge.backtester, "get_backtest_summary", return_value=mock_summary) as mock_sum:

            result = self.bridge.run_bridge_pipeline(
                symbol=self.symbol,
                shifts=random_shifts,
                percentage=random_percentage
            )

            mock_opt.assert_called_once_with(
                symbol=self.symbol,
                shifts=random_shifts,
                percentage=random_percentage
            )
            mock_bt.assert_called_once_with(
                symbol=self.symbol,
                initial_capital_or_shifts=random_shifts,
                strategy_params=mock_optimizer_result
            )
            mock_mdd.assert_called_once_with(mock_equity_curve)
            mock_sum.assert_called_once_with(self.symbol)

            self.assertEqual(result["optimizer_result"], mock_optimizer_result)
            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["maximum_drawdown"], mock_max_drawdown)
            self.assertEqual(result["equity_curve"], mock_equity_curve)

    def test_evaluate_bridge_resilience(self):
        random_shifts = random.randint(1, 10)
        expected_resilience = {
            str(uuid.uuid4().hex): random.randint(10, 100),
            "resilience_score": round(random.uniform(0.5, 1.0), 2)
        }

        with patch.object(self.bridge.optimizer, "evaluate_resilience", return_value=expected_resilience) as mock_eval:
            res = self.bridge.evaluate_bridge_resilience(self.symbol, random_shifts)

            mock_eval.assert_called_once_with(self.symbol, random_shifts)
            self.assertEqual(res, expected_resilience)

    def test_simulate_bridge_historical_trades(self):
        random_allocation = round(random.uniform(1000.0, 50000.0), 2)
        expected_trades = [
            {
                str(uuid.uuid4().hex): round(random.uniform(10.0, 100.0), 2),
                "action": random.choice(["BUY", "SELL"])
            }
            for _ in range(3)
        ]

        with patch.object(self.bridge.backtester, "simulate_historical_trades", return_value=expected_trades) as mock_sim:
            trades = self.bridge.simulate_bridge_historical_trades(self.symbol, random_allocation)

            mock_sim.assert_called_once_with(self.symbol, random_allocation)
            self.assertEqual(trades, expected_trades)

    def test_optimize_and_backtest_alias(self):
        random_shifts = random.randint(1, 5)
        random_percentage = round(random.uniform(0.01, 1.0), 2)
        expected_dict = {str(uuid.uuid4().hex): str(uuid.uuid4().hex)}

        with patch.object(self.bridge, "run_bridge_pipeline", return_value=expected_dict) as mock_pipeline:
            res = self.bridge.optimize_and_backtest(self.symbol, random_shifts, random_percentage)

            mock_pipeline.assert_called_once_with(self.symbol, random_shifts, random_percentage)
            self.assertEqual(res, expected_dict)


if __name__ == "__main__":
    unittest.main()