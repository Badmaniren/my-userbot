import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import string
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.initial_capital = round(random.uniform(1000.0, 100000.0), 2)
        self.strategy_params = {uuid.uuid4().hex: random.randint(1, 100)}

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_ensure_storage_exists_creates_file(self):
        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.assertFalse(os.path.exists(self.storage_file))
        bridge._ensure_storage_exists()
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_ensure_storage_exists_already_valid(self):
        expected_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w") as f:
            json.dump(expected_data, f)
        
        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        bridge._ensure_storage_exists()
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, expected_data)

    @patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics')
    def test_evaluate_backtest_performance(self, mock_analytics_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_metrics = {uuid.uuid4().hex: random.random()}
        expected_eval = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_analytics_instance.calculate_metrics.return_value = expected_metrics
        mock_analytics_instance.evaluate_performance.return_value = expected_eval

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        result = bridge.evaluate_backtest_performance(self.symbol)

        mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
        mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["performance_metrics"], expected_metrics)
        self.assertEqual(result["performance_evaluation"], expected_eval)

    @patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics')
    def test_run_comprehensive_evaluation(self, mock_analytics_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        expected_execution = {uuid.uuid4().hex: random.randint(1, 500)}
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_metrics = {uuid.uuid4().hex: random.random()}
        expected_evaluation = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_backtester_instance.run_backtest.return_value = expected_execution
        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_analytics_instance.calculate_metrics.return_value = expected_metrics
        mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        result = bridge.run_comprehensive_evaluation(self.symbol, self.initial_capital, self.strategy_params)

        mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
        mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

        self.assertEqual(result["backtest_execution"], expected_execution)
        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["metrics"], expected_metrics)
        self.assertEqual(result["evaluation"], expected_evaluation)

    @patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics')
    def test_evaluate_strategy_backtest(self, mock_analytics_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_metrics = {uuid.uuid4().hex: random.random()}
        expected_eval = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_analytics_instance.calculate_metrics.return_value = expected_metrics
        mock_analytics_instance.evaluate_performance.return_value = expected_eval

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        result = bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

        mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
        mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["performance_metrics"], expected_metrics)
        self.assertEqual(result["performance_evaluation"], expected_eval)

if __name__ == '__main__':
    unittest.main()