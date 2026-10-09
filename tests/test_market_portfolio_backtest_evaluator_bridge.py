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
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.initial_capital = round(random.uniform(1000.0, 100000.0), 2)
        self.strategy_params = {
            f"param_{uuid.uuid4().hex[:4]}": random.randint(1, 100),
            f"param_{uuid.uuid4().hex[:4]}": round(random.random(), 4)
        }
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_ensure_storage_exists_creates_file(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        
        self.assertFalse(os.path.exists(self.storage_file))
        self.bridge._ensure_storage_exists()
        self.assertTrue(os.path.exists(self.storage_file))
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_ensure_storage_exists_repairs_empty_file(self):
        with open(self.storage_file, "w") as f:
            f.write("")
        
        self.assertTrue(os.path.exists(self.storage_file))
        self.assertEqual(os.path.getsize(self.storage_file), 0)
        
        self.bridge._ensure_storage_exists()
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_evaluate_backtest_performance(self):
        expected_summary = {uuid.uuid4().hex: random.randint(1, 500)}
        expected_metrics = {uuid.uuid4().hex: round(random.uniform(0.1, 99.9), 2)}
        expected_evaluation = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as MockBacktester, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as MockAnalytics:
            
            instance_backtester = MockBacktester.return_value
            instance_backtester.get_backtest_summary.return_value = expected_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = expected_metrics
            instance_analytics.evaluate_performance.return_value = expected_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
            result = bridge.evaluate_backtest_performance(self.symbol)

            instance_backtester.get_backtest_summary.assert_called_once_with(self.symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

    def test_run_comprehensive_evaluation(self):
        expected_execution = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_summary = {uuid.uuid4().hex: random.randint(10, 100)}
        expected_metrics = {uuid.uuid4().hex: round(random.uniform(1.0, 50.0), 2)}
        expected_evaluation = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as MockBacktester, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as MockAnalytics:
            
            instance_backtester = MockBacktester.return_value
            instance_backtester.run_backtest.return_value = expected_execution
            instance_backtester.get_backtest_summary.return_value = expected_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = expected_metrics
            instance_analytics.evaluate_performance.return_value = expected_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
            result = bridge.run_comprehensive_evaluation(self.symbol, self.initial_capital, self.strategy_params)

            instance_backtester.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            instance_backtester.get_backtest_summary.assert_called_once_with(self.symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_execution"], expected_execution)
            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["metrics"], expected_metrics)
            self.assertEqual(result["evaluation"], expected_evaluation)

    def test_evaluate_strategy_backtest(self):
        expected_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_metrics = {uuid.uuid4().hex: round(random.uniform(0.01, 5.0), 4)}
        expected_evaluation = {uuid.uuid4().hex: random.choice([True, False])}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as MockBacktester, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as MockAnalytics:
            
            instance_backtester = MockBacktester.return_value
            instance_backtester.get_backtest_summary.return_value = expected_summary

            instance_analytics = MockAnalytics.return_value
            instance_analytics.calculate_metrics.return_value = expected_metrics
            instance_analytics.evaluate_performance.return_value = expected_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
            result = bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

            instance_backtester.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            instance_backtester.get_backtest_summary.assert_called_once_with(self.symbol)
            instance_analytics.calculate_metrics.assert_called_once_with(self.symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

if __name__ == "__main__":
    unittest.main()