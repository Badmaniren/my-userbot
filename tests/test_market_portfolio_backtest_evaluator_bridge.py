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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
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

    def test_evaluate_backtest_performance(self):
        expected_summary = {"status": uuid.uuid4().hex, "profit": random.uniform(100.0, 5000.0)}
        expected_metrics = {"sharpe": random.uniform(0.5, 3.0), "drawdown": random.uniform(0.01, 0.25)}
        expected_evaluation = {"grade": random.choice(["A", "B", "C", "D"]), "score": random.randint(50, 100)}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=expected_summary) as mock_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=expected_metrics) as mock_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=expected_evaluation) as mock_eval:

            result = self.bridge.evaluate_backtest_performance(self.symbol)

            mock_summary.assert_called_once_with(self.symbol)
            mock_metrics.assert_called_once_with(self.symbol)
            mock_eval.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

    def test_run_comprehensive_evaluation(self):
        initial_capital = random.uniform(10000.0, 100000.0)
        strategy_params = {uuid.uuid4().hex: random.randint(1, 100)}
        
        expected_execution = {"execution_id": uuid.uuid4().hex, "success": True}
        expected_summary = {"total_trades": random.randint(10, 50)}
        expected_metrics = {"roi": random.uniform(-0.1, 0.5)}
        expected_evaluation = {"approved": random.choice([True, False])}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest", return_value=expected_execution) as mock_run, \
             patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=expected_summary) as mock_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=expected_metrics) as mock_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=expected_evaluation) as mock_eval:

            result = self.bridge.run_comprehensive_evaluation(self.symbol, initial_capital, strategy_params)

            mock_run.assert_called_once_with(self.symbol, initial_capital, strategy_params)
            mock_summary.assert_called_once_with(self.symbol)
            mock_metrics.assert_called_once_with(self.symbol)
            mock_eval.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_execution"], expected_execution)
            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["metrics"], expected_metrics)
            self.assertEqual(result["evaluation"], expected_evaluation)

    def test_evaluate_strategy_backtest(self):
        initial_capital = random.uniform(5000.0, 50000.0)
        strategy_params = {uuid.uuid4().hex: uuid.uuid4().hex}

        expected_summary = {"summary_id": uuid.uuid4().hex}
        expected_metrics = {"volatility": random.uniform(0.1, 0.4)}
        expected_evaluation = {"rating": random.randint(1, 5)}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest") as mock_run, \
             patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=expected_summary) as mock_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=expected_metrics) as mock_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=expected_evaluation) as mock_eval:

            result = self.bridge.evaluate_strategy_backtest(self.symbol, initial_capital, strategy_params)

            mock_run.assert_called_once_with(self.symbol, initial_capital, strategy_params)
            mock_summary.assert_called_once_with(self.symbol)
            mock_metrics.assert_called_once_with(self.symbol)
            mock_eval.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

    def test_ensure_storage_exists_handles_corrupted_file(self):
        with open(self.storage_file, "w") as f:
            f.write("")

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertEqual(os.path.getsize(self.storage_file), 0)

        self.bridge._ensure_storage_exists()

        with open(self.storage_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main()