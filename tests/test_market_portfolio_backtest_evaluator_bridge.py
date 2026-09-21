import unittest
from unittest.mock import patch, MagicMock
import uuid
import random

from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.initial_capital = random.uniform(1000.0, 100000.0)
        self.shifts = [random.randint(1, 10) for _ in range(3)]
        self.strategy_params = {f"param_{uuid.uuid4().hex[:4]}": random.random()}

    @patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics")
    @patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester")
    def test_evaluate_backtest_performance_success(self, MockBacktester, MockAnalytics):
        mock_bt_instance = MockBacktester.return_value
        mock_an_instance = MockAnalytics.return_value

        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_metrics = {uuid.uuid4().hex: random.random()}
        expected_eval = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_bt_instance.get_backtest_summary.return_value = expected_summary
        mock_an_instance.calculate_metrics.return_value = expected_metrics
        mock_an_instance.evaluate_performance.return_value = expected_eval

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        result = bridge.evaluate_backtest_performance(self.symbol)

        MockBacktester.assert_called_once_with(self.storage_file)
        MockAnalytics.assert_called_once_with(self.storage_file)

        mock_bt_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_an_instance.calculate_metrics.assert_called_once_with(self.symbol)
        mock_an_instance.evaluate_performance.assert_called_once_with(self.symbol)

        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["performance_metrics"], expected_metrics)
        self.assertEqual(result["performance_evaluation"], expected_eval)

    @patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics")
    @patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester")
    def test_run_comprehensive_evaluation_success(self, MockBacktester, MockAnalytics):
        mock_bt_instance = MockBacktester.return_value
        mock_an_instance = MockAnalytics.return_value

        expected_execution = {uuid.uuid4().hex: random.uniform(1, 500)}
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_metrics = {uuid.uuid4().hex: random.random()}
        expected_eval = {uuid.uuid4().hex: True}

        mock_bt_instance.run_backtest.return_value = expected_execution
        mock_bt_instance.get_backtest_summary.return_value = expected_summary
        mock_an_instance.calculate_metrics.return_value = expected_metrics
        mock_an_instance.evaluate_performance.return_value = expected_eval

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        result = bridge.run_comprehensive_evaluation(self.symbol, self.shifts, self.strategy_params)

        MockBacktester.assert_called_once_with(self.storage_file)
        MockAnalytics.assert_called_once_with(self.storage_file)

        mock_bt_instance.run_backtest.assert_called_once_with(self.symbol, self.shifts, self.strategy_params)
        mock_bt_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_an_instance.calculate_metrics.assert_called_once_with(self.symbol)
        mock_an_instance.evaluate_performance.assert_called_once_with(self.symbol)

        self.assertEqual(result["backtest_execution"], expected_execution)
        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["metrics"], expected_metrics)
        self.assertEqual(result["evaluation"], expected_eval)

    @patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics")
    @patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester")
    def test_evaluate_strategy_backtest_success(self, MockBacktester, MockAnalytics):
        mock_bt_instance = MockBacktester.return_value
        mock_an_instance = MockAnalytics.return_value

        expected_summary = {uuid.uuid4().hex: random.randint(10, 99)}
        expected_metrics = {uuid.uuid4().hex: random.random()}
        expected_eval = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_bt_instance.get_backtest_summary.return_value = expected_summary
        mock_an_instance.calculate_metrics.return_value = expected_metrics
        mock_an_instance.evaluate_performance.return_value = expected_eval

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        result = bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

        MockBacktester.assert_called_once_with(self.storage_file)
        MockAnalytics.assert_called_once_with(self.storage_file)

        mock_bt_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
        mock_bt_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_an_instance.calculate_metrics.assert_called_once_with(self.symbol)
        mock_an_instance.evaluate_performance.assert_called_once_with(self.symbol)

        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["performance_metrics"], expected_metrics)
        self.assertEqual(result["performance_evaluation"], expected_eval)

    @patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics")
    @patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester")
    def test_bridge_initialization_passes_storage_file(self, MockBacktester, MockAnalytics):
        custom_storage = f"path_{uuid.uuid4().hex}.db"
        MarketPortfolioBacktestEvaluatorBridge(custom_storage)

        MockBacktester.assert_called_once_with(custom_storage)
        MockAnalytics.assert_called_once_with(custom_storage)

if __name__ == "__main__":
    unittest.main()