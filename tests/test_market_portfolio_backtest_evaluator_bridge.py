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
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}_{self.random_suffix}"
        self.initial_capital = float(random.randint(10000, 500000))
        self.strategy_params = {
            f"param_{uuid.uuid4().hex[:4]}": random.random()
            for _ in range(3)
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

    def test_ensure_storage_exists_handles_empty_file(self):
        with open(self.storage_file, "w") as f:
            f.write("")
            
        self.assertTrue(os.path.exists(self.storage_file))
        self.assertEqual(os.path.getsize(self.storage_file), 0)
        
        self.bridge._ensure_storage_exists()
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_evaluate_backtest_performance(self):
        mock_summary = {f"sum_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        mock_metrics = {f"met_{uuid.uuid4().hex[:4]}": random.uniform(0.1, 99.9)}
        mock_evaluation = {f"eval_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_get_summary, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_calc_metrics, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_eval_perf:

            result = self.bridge.evaluate_backtest_performance(self.symbol)

            mock_get_summary.assert_called_once_with(self.symbol)
            mock_calc_metrics.assert_called_once_with(self.symbol)
            mock_eval_perf.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

    def test_run_comprehensive_evaluation(self):
        mock_execution = {f"exec_{uuid.uuid4().hex[:4]}": random.randint(100, 200)}
        mock_summary = {f"sum_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        mock_metrics = {f"met_{uuid.uuid4().hex[:4]}": random.uniform(0.1, 99.9)}
        mock_evaluation = {f"eval_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}

        shifts_arg = float(random.randint(1, 10))

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.run_backtest', return_value=mock_execution) as mock_run, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_get_summary, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_calc_metrics, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_eval_perf:

            result = self.bridge.run_comprehensive_evaluation(self.symbol, shifts_arg, self.strategy_params)

            mock_run.assert_called_once_with(self.symbol, shifts_arg, self.strategy_params)
            mock_get_summary.assert_called_once_with(self.symbol)
            mock_calc_metrics.assert_called_once_with(self.symbol)
            mock_eval_perf.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_execution"], mock_execution)
            self.assertEqual(result["summary"], mock_summary)
            self.assertEqual(result["metrics"], mock_metrics)
            self.assertEqual(result["evaluation"], mock_evaluation)

    def test_evaluate_strategy_backtest(self):
        mock_summary = {f"sum_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        mock_metrics = {f"met_{uuid.uuid4().hex[:4]}": random.uniform(0.1, 99.9)}
        mock_evaluation = {f"eval_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.run_backtest') as mock_run, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_get_summary, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_calc_metrics, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_eval_perf:

            result = self.bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

            mock_run.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            mock_get_summary.assert_called_once_with(self.symbol)
            mock_calc_metrics.assert_called_once_with(self.symbol)
            mock_eval_perf.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

if __name__ == '__main__':
    unittest.main()