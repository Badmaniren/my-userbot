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
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_filename)

    def tearDown(self):
        if os.path.exists(self.random_filename):
            try:
                os.remove(self.random_filename)
            except OSError:
                pass

    def test_ensure_storage_exists_creates_file(self):
        if os.path.exists(self.random_filename):
            os.remove(self.random_filename)

        self.assertFalse(os.path.exists(self.random_filename))
        self.bridge._ensure_storage_exists()
        self.assertTrue(os.path.exists(self.random_filename))

        with open(self.random_filename, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_ensure_storage_exists_resets_empty_file(self):
        with open(self.random_filename, "w") as f:
            f.write("")

        self.assertTrue(os.path.exists(self.random_filename))
        self.assertEqual(os.path.getsize(self.random_filename), 0)

        self.bridge._ensure_storage_exists()

        with open(self.random_filename, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_evaluate_backtest_performance(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        mock_summary = {"summary_id": uuid.uuid4().hex, "status": random.choice(["PASS", "FAIL"])}
        mock_metrics = {"metric_score": random.random()}
        mock_evaluation = {"evaluation_result": uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_summary_patch, \
             patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_metrics_patch, \
             patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_eval_patch:

            result = self.bridge.evaluate_backtest_performance(symbol)

            mock_summary_patch.assert_called_once_with(symbol)
            mock_metrics_patch.assert_called_once_with(symbol)
            mock_eval_patch.assert_called_once_with(symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

    def test_run_comprehensive_evaluation(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        initial_capital = round(random.uniform(1000.0, 50000.0), 2)
        strategy_params = {uuid.uuid4().hex: random.randint(1, 100)}

        mock_execution = {"execution_id": uuid.uuid4().hex}
        mock_summary = {"summary_status": uuid.uuid4().hex}
        mock_metrics = {"alpha": random.uniform(-1.0, 1.0)}
        mock_evaluation = {"grade": random.choice(["A", "B", "C", "D"])}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=mock_execution) as mock_run_patch, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_summary_patch, \
             patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_metrics_patch, \
             patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_eval_patch:

            result = self.bridge.run_comprehensive_evaluation(symbol, initial_capital, strategy_params)

            mock_run_patch.assert_called_once_with(symbol, initial_capital, strategy_params)
            mock_summary_patch.assert_called_once_with(symbol)
            mock_metrics_patch.assert_called_once_with(symbol)
            mock_eval_patch.assert_called_once_with(symbol)

            self.assertEqual(result["backtest_execution"], mock_execution)
            self.assertEqual(result["summary"], mock_summary)
            self.assertEqual(result["metrics"], mock_metrics)
            self.assertEqual(result["evaluation"], mock_evaluation)

    def test_evaluate_strategy_backtest(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        initial_capital = round(random.uniform(5000.0, 100000.0), 2)
        strategy_params = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_summary = {"summary_key": uuid.uuid4().hex}
        mock_metrics = {"sharpe": random.uniform(0.0, 3.0)}
        mock_evaluation = {"approved": random.choice([True, False])}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest') as mock_run_patch, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_summary_patch, \
             patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_metrics_patch, \
             patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_eval_patch:

            result = self.bridge.evaluate_strategy_backtest(symbol, initial_capital, strategy_params)

            mock_run_patch.assert_called_once_with(symbol, initial_capital, strategy_params)
            mock_summary_patch.assert_called_once_with(symbol)
            mock_metrics_patch.assert_called_once_with(symbol)
            mock_eval_patch.assert_called_once_with(symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

if __name__ == '__main__':
    unittest.main()