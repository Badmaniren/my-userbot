import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"SYM_{''.join(random.choices(string.ascii_uppercase, k=4))}"
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)
        self.shifts = random.randint(1, 100)
        self.strategy_params = {
            f"param_{uuid.uuid4().hex[:4]}": random.choice([True, False, random.random()])
            for _ in range(3)
        }

    def test_evaluate_backtest_performance(self):
        mock_summary = {uuid.uuid4().hex: random.randint(10, 100)}
        mock_metrics = {uuid.uuid4().hex: random.uniform(0.1, 5.0)}
        mock_eval = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_bs, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_cm, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_eval) as mock_ep:
            
            result = self.bridge.evaluate_backtest_performance(self.symbol)

            mock_bs.assert_called_once_with(self.symbol)
            mock_cm.assert_called_once_with(self.symbol)
            mock_ep.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_eval)

    def test_run_comprehensive_evaluation(self):
        mock_execution = {uuid.uuid4().hex: random.randint(50, 500)}
        mock_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_metrics = {uuid.uuid4().hex: random.uniform(10.0, 99.9)}
        mock_evaluation = {uuid.uuid4().hex: random.choice([True, False])}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.run_backtest', return_value=mock_execution) as mock_rb, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_bs, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_cm, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_ep:

            result = self.bridge.run_comprehensive_evaluation(self.symbol, self.shifts, self.strategy_params)

            mock_rb.assert_called_once_with(self.symbol, self.shifts, self.strategy_params)
            mock_bs.assert_called_once_with(self.symbol)
            mock_cm.assert_called_once_with(self.symbol)
            mock_ep.assert_called_once_with(self.symbol)

            self.assertDictEqual(result, {
                "backtest_execution": mock_execution,
                "summary": mock_summary,
                "metrics": mock_metrics,
                "evaluation": mock_evaluation
            })

    def test_evaluate_strategy_backtest(self):
        mock_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_metrics = {uuid.uuid4().hex: random.uniform(-5.0, 5.0)}
        mock_evaluation = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.run_backtest') as mock_rb, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester.get_backtest_summary', return_value=mock_summary) as mock_bs, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.calculate_metrics', return_value=mock_metrics) as mock_cm, \
             patch('skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics.evaluate_performance', return_value=mock_evaluation) as mock_ep:

            result = self.bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

            mock_rb.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            mock_bs.assert_called_once_with(self.symbol)
            mock_cm.assert_called_once_with(self.symbol)
            mock_ep.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["performance_metrics"], mock_metrics)
            self.assertEqual(result["performance_evaluation"], mock_evaluation)

if __name__ == '__main__':
    unittest.main()