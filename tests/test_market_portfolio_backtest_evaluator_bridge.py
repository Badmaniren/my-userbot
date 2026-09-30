import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.initial_capital = round(random.uniform(1000.0, 100000.0), 2)
        self.strategy_params = {
            "".join(random.choices(string.ascii_lowercase, k=4)): random.randint(1, 100)
            for _ in range(3)
        }
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)

    def test_evaluate_backtest_performance(self):
        expected_summary = {"summary_id": uuid.uuid4().hex, "status": "completed"}
        expected_metrics = {"roi": round(random.uniform(-0.5, 2.0), 4)}
        expected_evaluation = {"score": random.randint(1, 10)}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as mock_backtester_cls, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as mock_analytics_cls:
            
            mock_backtester_instance = mock_backtester_cls.return_value
            mock_backtester_instance.get_backtest_summary.return_value = expected_summary

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = expected_metrics
            mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
            result = bridge.evaluate_backtest_performance(self.symbol)

            mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

    def test_run_comprehensive_evaluation(self):
        expected_execution = {"execution_id": uuid.uuid4().hex, "trades": random.randint(5, 50)}
        expected_summary = {"summary_id": uuid.uuid4().hex}
        expected_metrics = {"sharpe_ratio": round(random.uniform(0.1, 3.0), 2)}
        expected_evaluation = {"passed": True}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as mock_backtester_cls, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as mock_analytics_cls:
            
            mock_backtester_instance = mock_backtester_cls.return_value
            mock_backtester_instance.run_backtest.return_value = expected_execution
            mock_backtester_instance.get_backtest_summary.return_value = expected_summary

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = expected_metrics
            mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
            result = bridge.run_comprehensive_evaluation(self.symbol, self.initial_capital, self.strategy_params)

            mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_execution"], expected_execution)
            self.assertEqual(result["summary"], expected_summary)
            self.assertEqual(result["metrics"], expected_metrics)
            self.assertEqual(result["evaluation"], expected_evaluation)

    def test_evaluate_strategy_backtest(self):
        expected_summary = {"summary_id": uuid.uuid4().hex, "profit": random.randint(100, 5000)}
        expected_metrics = {"max_drawdown": round(random.uniform(0.01, 0.25), 4)}
        expected_evaluation = {"rating": ''.join(random.choices(string.ascii_uppercase, k=1))}

        with patch("skills.market_portfolio_backtest_evaluator_bridge.MarketPortfolioBacktester") as mock_backtester_cls, \
             patch("skills.market_portfolio_backtest_evaluator_bridge.PortfolioPerformanceAnalytics") as mock_analytics_cls:
            
            mock_backtester_instance = mock_backtester_cls.return_value
            mock_backtester_instance.get_backtest_summary.return_value = expected_summary

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = expected_metrics
            mock_analytics_instance.evaluate_performance.return_value = expected_evaluation

            bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
            result = bridge.evaluate_strategy_backtest(self.symbol, self.initial_capital, self.strategy_params)

            mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.initial_capital, self.strategy_params)
            mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)

            self.assertEqual(result["backtest_summary"], expected_summary)
            self.assertEqual(result["performance_metrics"], expected_metrics)
            self.assertEqual(result["performance_evaluation"], expected_evaluation)

if __name__ == "__main__":
    unittest.main()