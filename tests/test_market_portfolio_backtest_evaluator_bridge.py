import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_capital = round(random.uniform(1000.0, 100000.0), 2)
        self.random_strategy_param = {uuid.uuid4().hex: random.randint(1, 100)}

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_ensure_storage_exists_creates_file(self):
        bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
        self.assertFalse(os.path.exists(self.random_storage))
        
        bridge._ensure_storage_exists()
        
        self.assertTrue(os.path.exists(self.random_storage))
        with open(self.random_storage, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_evaluate_backtest_performance_success(self):
        mock_summary = {uuid.uuid4().hex: random.randint(1, 50)}
        mock_metrics = {uuid.uuid4().hex: random.random()}
        mock_evaluation = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester') as MockBacktester, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics') as MockAnalytics:
            
            instance_backtester = MockBacktester.return_value
            instance_backtester.get_backtest_summary.return_value = mock_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = mock_metrics
            instance_analytics.evaluate_performance.return_value = mock_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
            result = bridge.evaluate_backtest_performance(self.random_symbol)

            instance_backtester.get_backtest_summary.assert_called_once_with(self.random_symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.random_symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.random_symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

    def test_run_comprehensive_evaluation_success(self):
        mock_execution = {uuid.uuid4().hex: random.random()}
        mock_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_metrics = {uuid.uuid4().hex: random.randint(100, 500)}
        mock_evaluation = {uuid.uuid4().hex: True}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester') as MockBacktester, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics') as MockAnalytics:
            
            instance_backtester = MockBacktester.return_value
            instance_backtester.run_backtest.return_value = mock_execution
            instance_backtester.get_backtest_summary.return_value = mock_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = mock_metrics
            instance_analytics.evaluate_performance.return_value = mock_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
            result = bridge.run_comprehensive_evaluation(self.random_symbol, self.random_capital, self.random_strategy_param)

            instance_backtester.run_backtest.assert_called_once_with(self.random_symbol, self.random_capital, self.random_strategy_param)
            instance_backtester.get_backtest_summary.assert_called_once_with(self.random_symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.random_symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.random_symbol)

            self.assertEqual(result["backtest_execution"], mock_execution)
            self.assertEqual(result["summary"], mock_summary)
            self.assertEqual(result["metrics"], mock_metrics)
            self.assertEqual(result["evaluation"], mock_evaluation)

    def test_evaluate_strategy_backtest_success(self):
        mock_summary = {uuid.uuid4().hex: random.uniform(1.0, 10.0)}
        mock_metrics = {uuid.uuid4().hex: random.uniform(10.0, 100.0)}
        mock_evaluation = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester') as MockBacktester, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics') as MockAnalytics:
            
            instance_backtester = MockBacktester.return_value
            instance_backtester.get_backtest_summary.return_value = mock_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = mock_metrics
            instance_analytics.evaluate_performance.return_value = mock_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
            result = bridge.evaluate_strategy_backtest(self.random_symbol, self.random_capital, self.random_strategy_param)

            instance_backtester.run_backtest.assert_called_once_with(self.random_symbol, self.random_capital, self.random_strategy_param)
            instance_backtester.get_backtest_summary.assert_called_once_with(self.random_symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.random_symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.random_symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

if __name__ == '__main__':
    unittest.main()