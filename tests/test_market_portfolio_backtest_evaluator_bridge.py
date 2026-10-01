import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io

class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):

    def setUp(self):
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)
        self.strategy_params = {
            "param_a": random.randint(1, 100),
            "param_b": round(random.uniform(0.1, 5.0), 2)
        }

    def tearDown(self):
        if os.path.exists(self.random_filename):
            try:
                os.remove(self.random_filename)
            except OSError:
                pass

    def test_ensure_storage_exists_creates_file(self):
        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester'), \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics'):
            
            from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge
            
            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_filename)
            bridge._ensure_storage_exists()

            self.assertTrue(os.path.exists(self.random_filename))
            with open(self.random_filename, "r") as f:
                content = json.load(f)
                self.assertEqual(content, {})

    def test_ensure_storage_exists_handles_existing_valid_file(self):
        expected_data = {str(uuid.uuid4()): random.randint(1, 100)}
        with open(self.random_filename, "w") as f:
            json.dump(expected_data, f)

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester'), \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics'):
            
            from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge
            
            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_filename)
            bridge._ensure_storage_exists()

            with open(self.random_filename, "r") as f:
                content = json.load(f)
                self.assertEqual(content, expected_data)

    def test_evaluate_backtest_performance(self):
        mock_summary = {"summary_id": uuid.uuid4().hex, "profit": random.randint(100, 1000)}
        mock_metrics = {"sharpe": random.uniform(0.5, 3.0)}
        mock_eval = {"status": random.choice(["PASS", "FAIL"])}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester') as mock_backtester_cls, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics') as mock_analytics_cls:
            
            mock_backtester_instance = mock_backtester_cls.return_value
            mock_backtester_instance.get_backtest_summary.return_value = mock_summary

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = mock_metrics
            mock_analytics_instance.evaluate_performance.return_value = mock_eval

            from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_filename)
            result = bridge.evaluate_backtest_performance(self.symbol)

            mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_eval)

    def test_run_comprehensive_evaluation(self):
        mock_execution = {"execution_id": uuid.uuid4().hex, "success": True}
        mock_summary = {"summary_id": uuid.uuid4().hex, "roi": random.uniform(0.01, 0.5)}
        mock_metrics = {"max_drawdown": random.uniform(-0.5, -0.05)}
        mock_eval = {"score": random.randint(50, 100)}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester') as mock_backtester_cls, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics') as mock_analytics_cls:
            
            mock_backtester_instance = mock_backtester_cls.return_value
            mock_backtester_instance.run_backtest.return_value = mock_execution
            mock_backtester_instance.get_backtest_summary.return_value = mock_summary

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = mock_metrics
            mock_analytics_instance.evaluate_performance.return_value = mock_eval

            from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_filename)
            result = bridge.run_comprehensive_evaluation(self.symbol, self.initial_capital, self.strategy_params)

            mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_execution"], mock_execution)
            self.assertEqual(result["summary"], mock_summary)
            self.assertEqual(result["metrics"], mock_metrics)
            self.assertEqual(result["evaluation"], mock_eval)

    def test_evaluate_strategy_backtest(self):
        mock_summary = {"summary_id": uuid.uuid4().hex, "trades_count": random.randint(5, 50)}
        mock_metrics = {"alpha": random.uniform(0.0, 0.2)}
        mock_eval = {"recommendation": random.choice(["BUY", "HOLD", "SELL"])}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester') as mock_backtester_cls, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics') as mock_analytics_cls:
            
            mock_backtester_instance = mock_backtester_cls.return_value
            mock_backtester_instance.get_backtest_summary.return_value = mock_summary

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = mock_metrics
            mock_analytics_instance.evaluate_performance.return_value = mock_eval

            from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_filename)
            result = bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

            mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_eval)

if __name__ == '__main__':
    unittest.main()