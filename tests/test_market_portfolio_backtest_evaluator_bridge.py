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
        self.storage_file = f"{uuid.uuid4().hex}.json"
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
        
        self.bridge._ensure_storage_exists()
        
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data, {})

    def test_ensure_storage_exists_handles_empty_file(self):
        with open(self.storage_file, "w") as f:
            f.write("")
            
        self.assertTrue(os.path.getsize(self.storage_file) == 0)
        self.bridge._ensure_storage_exists()
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data, {})

    def test_evaluate_backtest_performance(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        expected_summary = {"summary_id": uuid.uuid4().hex}
        expected_metrics = {"metric_val": random.uniform(1.0, 100.0)}
        expected_evaluation = {"eval_status": random.choice(["PASS", "FAIL"])}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=expected_summary) as mock_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=expected_metrics) as mock_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=expected_evaluation) as mock_eval:

            result = self.bridge.evaluate_backtest_performance(rand_symbol)

            mock_summary.assert_called_once_with(rand_symbol)
            mock_metrics.assert_called_once_with(rand_symbol)
            mock_eval.assert_called_once_with(rand_symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

    def test_run_comprehensive_evaluation(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        rand_capital = random.uniform(1000.0, 50000.0)
        rand_param_key = uuid.uuid4().hex
        rand_param_val = random.randint(1, 100)
        strategy_params = {rand_param_key: rand_param_val}

        expected_execution = {"execution_id": uuid.uuid4().hex}
        expected_summary = {"summary_id": uuid.uuid4().hex}
        expected_metrics = {"metric_val": random.uniform(1.0, 100.0)}
        expected_evaluation = {"eval_status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest", return_value=expected_execution) as mock_run, \
             patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=expected_summary) as mock_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=expected_metrics) as mock_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=expected_evaluation) as mock_eval:

            result = self.bridge.run_comprehensive_evaluation(rand_symbol, rand_capital, strategy_params)

            mock_run.assert_called_once_with(rand_symbol, rand_capital, strategy_params)
            mock_summary.assert_called_once_with(rand_symbol)
            mock_metrics.assert_called_once_with(rand_symbol)
            mock_eval.assert_called_once_with(rand_symbol)

            self.assertEqual(result["backtest_execution"], expected_execution)
            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["metrics"], expected_metrics)
            self.assertEqual(result["evaluation"], expected_evaluation)

    def test_evaluate_strategy_backtest(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        rand_capital = random.uniform(500.0, 10000.0)
        strategy_params = {uuid.uuid4().hex: random.random()}

        expected_summary = {"summary": uuid.uuid4().hex}
        expected_metrics = {"metrics": uuid.uuid4().hex}
        expected_evaluation = {"eval": uuid.uuid4().hex}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest") as mock_run, \
             patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=expected_summary) as mock_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=expected_metrics) as mock_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=expected_evaluation) as mock_eval:

            result = self.bridge.evaluate_strategy_backtest(rand_symbol, rand_capital, strategy_params)

            mock_run.assert_called_once_with(rand_symbol, rand_capital, strategy_params)
            mock_summary.assert_called_once_with(rand_symbol)
            mock_metrics.assert_called_once_with(rand_symbol)
            mock_eval.assert_called_once_with(rand_symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

if __name__ == '__main__':
    unittest.main()