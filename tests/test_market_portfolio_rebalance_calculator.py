import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_rebalance_calculator import PortfolioRebalanceCalculator

class TestPortfolioRebalanceCalculator(unittest.TestCase):

    def test_init_with_string_path(self):
        rand_path = uuid.uuid4().hex + ".db"
        with patch('skills.market_portfolio_rebalance_calculator.PortfolioPerformanceAnalytics') as mock_analytics_cls, \
             patch('skills.market_portfolio_rebalance_calculator.PortfolioStrategyOptimizer') as mock_optimizer_cls:

            calc = PortfolioRebalanceCalculator(rand_path)

            self.assertEqual(calc.storage_file, rand_path)
            mock_analytics_cls.assert_called_once_with(rand_path)
            mock_optimizer_cls.assert_called_once_with(rand_path)

    def test_init_with_objects_custom_optimizer(self):
        mock_analytics = MagicMock()
        mock_optimizer = MagicMock()

        calc = PortfolioRebalanceCalculator(mock_analytics, mock_optimizer)

        self.assertEqual(calc.analytics, mock_analytics)
        self.assertEqual(calc.optimizer, mock_optimizer)

    def test_init_with_objects_default_optimizer(self):
        mock_analytics = MagicMock()
        with patch('skills.market_portfolio_rebalance_calculator.PortfolioStrategyOptimizer') as mock_optimizer_cls:
            mock_default_opt = MagicMock()
            mock_optimizer_cls.return_value = mock_default_opt

            calc = PortfolioRebalanceCalculator(mock_analytics, None)

            self.assertEqual(calc.analytics, mock_analytics)
            self.assertEqual(calc.optimizer, mock_default_opt)
            mock_optimizer_cls.assert_called_once_with(None)

    def test_calculate_rebalance_delegation_and_structure(self):
        symbol = "SYM_" + uuid.uuid4().hex[:6]
        shifts = random.uniform(0.01, 0.5)
        percentage = random.uniform(10.0, 100.0)

        mock_analytics = MagicMock()
        rand_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_analytics.calculate_metrics.return_value = rand_metrics

        mock_optimizer = MagicMock()
        rand_strategy = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_optimizer.optimize_strategy.return_value = rand_strategy

        calc = PortfolioRebalanceCalculator(mock_analytics, mock_optimizer)
        result = calc.calculate_rebalance(symbol, shifts, percentage)

        mock_analytics.calculate_metrics.assert_called_once_with(symbol)
        mock_optimizer.optimize_strategy.assert_called_once_with(symbol, shifts, percentage)

        self.assertEqual(result["target_weights"], {symbol: percentage})
        self.assertEqual(result["deviations"], {symbol: shifts})
        self.assertEqual(result["metrics"], rand_metrics)
        self.assertEqual(result["strategy"], rand_strategy)

    def test_evaluate_rebalance_strategy_delegation(self):
        symbol = "SYM_" + uuid.uuid4().hex[:6]
        shifts = random.uniform(0.05, 0.99)

        mock_analytics = MagicMock()
        rand_perf = {uuid.uuid4().hex: random.random()}
        mock_analytics.evaluate_performance.return_value = rand_perf

        mock_optimizer = MagicMock()
        rand_resilience = {uuid.uuid4().hex: random.random()}
        mock_optimizer.evaluate_resilience.return_value = rand_resilience

        calc = PortfolioRebalanceCalculator(mock_analytics, mock_optimizer)
        result = calc.evaluate_rebalance_strategy(symbol, shifts)

        mock_analytics.evaluate_performance.assert_called_once_with(symbol)
        mock_optimizer.evaluate_resilience.assert_called_once_with(symbol, shifts)

        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["performance_evaluation"], rand_perf)
        self.assertEqual(result["resilience_evaluation"], rand_resilience)

    def test_analyze_stream_and_summary_delegation(self):
        filepath = uuid.uuid4().hex + ".json"
        symbol = "SYM_" + uuid.uuid4().hex[:6]

        mock_analytics = MagicMock()
        mock_optimizer = MagicMock()

        rand_stream = [uuid.uuid4().hex, random.randint(1, 50)]
        rand_summary = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_optimizer.load_strategy_stream.return_value = rand_stream
        mock_optimizer.get_strategy_summary.return_value = rand_summary

        calc = PortfolioRebalanceCalculator(mock_analytics, mock_optimizer)
        result = calc.analyze_stream_and_summary(filepath, symbol)

        mock_optimizer.load_strategy_stream.assert_called_once_with(filepath)
        mock_optimizer.get_strategy_summary.assert_called_once_with(symbol)

        self.assertEqual(result["stream_data"], rand_stream)
        self.assertEqual(result["summary"], rand_summary)

    def test_full_rebalance_cycle_delegation(self):
        symbol = "SYM_" + uuid.uuid4().hex[:6]
        allocation = random.uniform(10, 500)
        shifts = random.uniform(0.1, 0.8)

        mock_analytics = MagicMock()
        mock_optimizer = MagicMock()

        rand_eval = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_optimizer.optimize_and_evaluate.return_value = rand_eval

        calc = PortfolioRebalanceCalculator(mock_analytics, mock_optimizer)
        result = calc.full_rebalance_cycle(symbol, allocation, shifts)

        mock_optimizer.optimize_and_evaluate.assert_called_once_with(symbol, allocation, shifts)
        self.assertEqual(result, rand_eval)