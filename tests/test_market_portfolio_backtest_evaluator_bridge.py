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
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            os.remove(self.random_storage)

    def test_ensure_storage_exists_creates_file(self):
        if os.path.exists(self.random_storage):
            os.remove(self.random_storage)
        
        self.bridge._ensure_storage_exists()
        
        self.assertTrue(os.path.exists(self.random_storage))
        with open(self.random_storage, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_ensure_storage_exists_handles_empty_file(self):
        with open(self.random_storage, "w") as f:
            f.write("")
            
        self.bridge._ensure_storage_exists()
        
        with open(self.random_storage, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    @patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics')
    def test_evaluate_backtest_performance(self, mock_analytics_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        expected_summary = {"summary_id": uuid.uuid4().hex, "status": random.choice(["OK", "FAIL"])}
        expected_metrics = {"sharpe": random.uniform(0.1, 3.0)}
        expected_evaluation = {"grade": random.choice(["A", "B", "C"])}

        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_analytics_instance.calculate_metrics.return_value = expected_metrics
        mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
        result = bridge.evaluate_backtest_performance(random_symbol)

        mock_backtester_instance.get_backtest_summary.assert_called_once_with(random_symbol)
        mock_analytics_instance.calculate_metrics.assert_called_once_with(random_symbol)
        mock_analytics_instance.evaluate_performance.assert_called_once_with(random_symbol)

        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["performance_metrics"], expected_metrics)
        self.assertEqual(result["performance_evaluation"], expected_evaluation)

    @patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics')
    def test_run_comprehensive_evaluation(self, mock_analytics_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        initial_capital = random.uniform(10000.0, 1000000.0)
        strategy_params = {"param_uuid": uuid.uuid4().hex, "risk_level": random.randint(1, 5)}

        expected_execution = {"execution_id": uuid.uuid4().hex}
        expected_summary = {"summary_id": uuid.uuid4().hex}
        expected_metrics = {"metrics_id": uuid.uuid4().hex}
        expected_evaluation = {"eval_id": uuid.uuid4().hex}

        mock_backtester_instance.run_backtest.return_value = expected_execution
        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_analytics_instance.calculate_metrics.return_value = expected_metrics
        mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
        result = bridge.run_comprehensive_evaluation(random_symbol, initial_capital, strategy_params)

        mock_backtester_instance.run_backtest.assert_called_once_with(random_symbol, initial_capital, strategy_params)
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(random_symbol)
        mock_analytics_instance.calculate_metrics.assert_called_once_with(random_symbol)
        mock_analytics_instance.evaluate_performance.assert_called_once_with(random_symbol)

        self.assertEqual(result["backtest_execution"], expected_execution)
        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["metrics"], expected_metrics)
        self.assertEqual(result["evaluation"], expected_evaluation)

    @patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics')
    def test_evaluate_strategy_backtest(self, mock_analytics_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_analytics_instance = mock_analytics_cls.return_value

        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        initial_capital = random.uniform(5000.0, 50000.0)
        strategy_params = {"strategy_uuid": uuid.uuid4().hex}

        expected_summary = {"summary_token": uuid.uuid4().hex}
        expected_metrics = {"metric_token": uuid.uuid4().hex}
        expected_evaluation = {"eval_token": uuid.uuid4().hex}

        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_analytics_instance.calculate_metrics.return_value = expected_metrics
        mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

        bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)
        result = bridge.evaluate_strategy_backtest(random_symbol, initial_capital, strategy_params)

        mock_backtester_instance.run_backtest.assert_called_once_with(random_symbol, initial_capital, strategy_params)
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(random_symbol)
        mock_analytics_instance.calculate_metrics.assert_called_once_with(random_symbol)
        mock_analytics_instance.evaluate_performance.assert_called_once_with(random_symbol)

        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["performance_metrics"], expected_metrics)
        self.assertEqual(result["performance_evaluation"], expected_evaluation)

if __name__ == '__main__':
    unittest.main()