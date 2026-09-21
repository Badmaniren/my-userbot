import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json

from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge


class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.evaluator_bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)

    def test_init_sets_storage(self):
        self.assertEqual(self.evaluator_bridge.storage_file, self.storage_file)

    def test_evaluate_backtest_composition_success(self):
        mock_equity_curve = [random.uniform(100, 200) for _ in range(5)]
        mock_summary = {
            f"metric_{uuid.uuid4().hex[:4]}": random.uniform(1, 100),
            "equity_curve": mock_equity_curve
        }
        mock_metrics = {
            f"perf_{uuid.uuid4().hex[:4]}": random.uniform(0.1, 5.0)
        }
        mock_eval_result = {
            f"eval_{uuid.uuid4().hex[:4]}": f"status_{uuid.uuid4().hex[:4]}"
        }

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as MockBacktester, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as MockAnalytics:

            instance_backtester = MockBacktester.return_value
            instance_backtester.get_backtest_summary.return_value = mock_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = mock_metrics
            instance_analytics.evaluate_performance.return_value = mock_eval_result

            result = self.evaluator_bridge.evaluate_backtest_performance(self.symbol)

            MockBacktester.assert_called_once_with(self.storage_file)
            MockAnalytics.assert_called_once_with(self.storage_file)

            instance_backtester.get_backtest_summary.assert_called_once_with(self.symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertIn("backtest_summary", result)
            self.assertIn("performance_metrics", result)
            self.assertIn("performance_evaluation", result)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_eval_result)

    def test_run_comprehensive_evaluation_pipeline(self):
        mock_shifts = random.randint(1, 30)
        mock_capital = random.uniform(1000, 50000)
        mock_strategy_params = {uuid.uuid4().hex: random.random()}

        mock_backtest_run_res = {uuid.uuid4().hex: random.random()}
        mock_summary = {uuid.uuid4().hex: "passed"}
        mock_metrics = {uuid.uuid4().hex: 123.45}
        mock_eval = {uuid.uuid4().hex: "optimal"}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as MockBacktester, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as MockAnalytics:

            bt_inst = MockBacktester.return_value
            bt_inst.run_backtest.return_value = mock_backtest_run_res
            bt_inst.get_backtest_summary.return_value = mock_summary

            an_inst = MockAnalytics.return_value
            an_inst.calculate_metrics.return_value = mock_metrics
            an_inst.evaluate_performance.return_value = mock_eval

            res = self.evaluator_bridge.run_comprehensive_evaluation(
                symbol=self.symbol,
                initial_capital_or_shifts=mock_shifts,
                strategy_params=mock_strategy_params
            )

            bt_inst.run_backtest.assert_called_once_with(self.symbol, mock_shifts, mock_strategy_params)
            bt_inst.get_backtest_summary.assert_called_once_with(self.symbol)

            an_inst.calculate_metrics.assert_called_once_with(self.symbol)
            an_inst.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(res["backtest_execution"], mock_backtest_run_res)
            self.assertEqual(res["summary"], mock_summary)
            self.assertEqual(res["metrics"], mock_metrics)
            self.assertEqual(res["evaluation"], mock_eval)


if __name__ == "__main__":
    unittest.main()