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
        self.random_storage = f"test_storage_{uuid.uuid4().hex}.json"
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.random_storage)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

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

    def test_evaluate_backtest_performance(self):
        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        mock_summary = {"summary_id": uuid.uuid4().hex, "status": random.choice(["SUCCESS", "FAILED"])}
        mock_metrics = {"sharpe": random.uniform(0.5, 3.0), "drawdown": random.uniform(0.01, 0.2)}
        mock_eval = {"grade": random.choice(["A", "B", "C"]), "score": random.randint(50, 100)}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=mock_summary) as mock_get_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=mock_metrics) as mock_calc_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=mock_eval) as mock_eval_perf:

            result = self.bridge.evaluate_backtest_performance(random_symbol)

            mock_get_summary.assert_called_once_with(random_symbol)
            mock_calc_metrics.assert_called_once_with(random_symbol)
            mock_eval_perf.assert_called_once_with(random_symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_eval)

    def test_run_comprehensive_evaluation(self):
        random_symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_capital = round(random.uniform(1000.0, 100000.0), 2)
        random_params = {uuid.uuid4().hex: random.randint(1, 100)}
        
        mock_execution = {"exec_id": uuid.uuid4().hex, "pnl": random.uniform(-500, 1500)}
        mock_summary = {"summary_id": uuid.uuid4().hex}
        mock_metrics = {"volatility": random.uniform(0.1, 0.5)}
        mock_eval = {"passed": random.choice([True, False])}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest", return_value=mock_execution) as mock_run, \
             patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=mock_summary) as mock_get_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=mock_metrics) as mock_calc_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=mock_eval) as mock_eval_perf:

            result = self.bridge.run_comprehensive_evaluation(random_symbol, random_capital, random_params)

            mock_run.assert_called_once_with(random_symbol, random_capital, random_params)
            mock_get_summary.assert_called_once_with(random_symbol)
            mock_calc_metrics.assert_called_once_with(random_symbol)
            mock_eval_perf.assert_called_once_with(random_symbol)

            self.assertEqual(result["backtest_execution"], mock_execution)
            self.assertEqual(result["summary"], mock_summary)
            self.assertEqual(result["metrics"], mock_metrics)
            self.assertEqual(result["evaluation"], mock_eval)

    def test_evaluate_strategy_backtest(self):
        random_symbol = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        random_capital = round(random.uniform(5000.0, 50000.0), 2)
        random_params = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_summary = {"summary": uuid.uuid4().hex}
        mock_metrics = {"alpha": random.uniform(-0.1, 0.3)}
        mock_eval = {"status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest") as mock_run, \
             patch("skills.market_portfolio_backtester.MarketPortfolioBacktester.get_backtest_summary", return_value=mock_summary) as mock_get_summary, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.calculate_metrics", return_value=mock_metrics) as mock_calc_metrics, \
             patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.evaluate_performance", return_value=mock_eval) as mock_eval_perf:

            result = self.bridge.evaluate_strategy_backtest(random_symbol, random_capital, random_params)

            mock_run.assert_called_once_with(random_symbol, random_capital, random_params)
            mock_get_summary.assert_called_once_with(random_symbol)
            mock_calc_metrics.assert_called_once_with(random_symbol)
            mock_eval_perf.assert_called_once_with(random_symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_eval)

    def test_io_operations_with_random_stream(self):
        random_bytes = uuid.uuid4().bytes + b"\x00\x01\x02"
        stream = io.BytesIO(random_bytes)
        self.assertIsNotNone(stream.read())

if __name__ == "__main__":
    unittest.main()