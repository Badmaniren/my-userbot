import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_backtest_runner import (
    MarketPortfolioStressBacktestRunner,
    run_stress_backtest_pipeline
)

class TestMarketPortfolioStressBacktestRunner(unittest.TestCase):

    def setUp(self):
        self.random_filepath = f"{uuid.uuid4().hex}_{uuid.uuid4().hex}.csv"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_capital = random.uniform(10000.0, 1000000.0)
        self.random_percentage = random.uniform(5.0, 50.0)
        self.random_shifts = random.randint(1, 100)

        self.strategy_params = {
            "window": random.randint(10, 50),
            "threshold": random.uniform(0.01, 0.05),
            "metric": uuid.uuid4().hex
        }

    def test_runner_initialization_and_composition(self):
        runner = MarketPortfolioStressBacktestRunner(self.random_filepath)

        self.assertEqual(runner.filepath, self.random_filepath)
        self.assertIsNotNone(runner.backtester)
        self.assertIsNotNone(runner.stress_pipeline)

    @patch('skills.market_portfolio_stress_backtest_runner.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_stress_backtest_runner.PortfolioStressScenarioPipeline')
    def test_run_stress_backtest_execution_flow(self, mock_pipeline_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_pipeline_instance = mock_pipeline_cls.return_value

        expected_summary = {
            "symbol": self.random_symbol,
            "net_profit": random.uniform(1000, 50000),
            "status": uuid.uuid4().hex
        }
        mock_backtester_instance.get_backtest_summary.return_value = expected_summary

        expected_stress_result = {
            "stressed": True,
            "impact": random.uniform(-0.5, -0.1),
            "token": uuid.uuid4().hex
        }
        mock_pipeline_instance.execute.return_value = expected_stress_result

        runner = MarketPortfolioStressBacktestRunner(self.random_filepath)
        report = runner.run_stress_backtest(
            symbol=self.random_symbol,
            initial_capital=self.random_capital,
            strategy_params=self.strategy_params,
            percentage=self.random_percentage,
            shifts=self.random_shifts
        )

        mock_backtester_instance.load_data.assert_called_once_with(self.random_filepath)
        mock_pipeline_instance.execute.assert_called_once_with(
            symbol=self.random_symbol,
            percentage=self.random_percentage,
            shifts=self.random_shifts
        )
        mock_backtester_instance.run_backtest.assert_called_once_with(
            symbol=self.random_symbol,
            initial_capital_or_shifts=self.random_capital,
            strategy_params=self.strategy_params
        )
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.random_symbol)

        self.assertIn("backtest_summary", report)
        self.assertIn("stress_scenario_result", report)
        self.assertEqual(report["backtest_summary"], expected_summary)
        self.assertEqual(report["stress_scenario_result"], expected_stress_result)
        self.assertEqual(report["symbol"], self.random_symbol)

    @patch('skills.market_portfolio_stress_backtest_runner.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_stress_backtest_runner.PortfolioStressScenarioPipeline')
    def test_standalone_pipeline_function(self, mock_pipeline_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_pipeline_instance = mock_pipeline_cls.return_value

        expected_summary = {
            "symbol": self.random_symbol,
            "max_drawdown": random.uniform(0.1, 0.9),
            "uuid": uuid.uuid4().hex
        }
        mock_backtester_instance.get_backtest_summary.return_value = expected_summary

        expected_stress_result = {
            "executed": True,
            "shift_count": self.random_shifts
        }
        mock_pipeline_instance.execute.return_value = expected_stress_result

        result_report = run_stress_backtest_pipeline(
            storage_file=self.random_filepath,
            symbol=self.random_symbol,
            initial_capital=self.random_capital,
            strategy_params=self.strategy_params,
            percentage=self.random_percentage,
            shifts=self.random_shifts
        )

        mock_backtester_instance.load_data.assert_called_once_with(self.random_filepath)
        self.assertEqual(result_report["backtest_summary"], expected_summary)
        self.assertEqual(result_report["stress_scenario_result"], expected_stress_result)

    def test_io_stream_behavior_with_random_bytes(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_file_stream = io.BytesIO(random_bytes)

        runner = MarketPortfolioStressBacktestRunner(self.random_filepath)

        with patch.object(runner.backtester, 'load_data') as mock_load:
            runner.backtester.load_data(mock_file_stream)
            mock_load.assert_called_once()
            args, _ = mock_load.call_args
            content = args[0].read()
            self.assertEqual(content, random_bytes)

    @patch('skills.market_portfolio_stress_backtest_runner.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_stress_backtest_runner.PortfolioStressScenarioPipeline')
    def test_validation_report_integrity(self, mock_pipeline_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value

        unique_summary_metric = uuid.uuid4().hex
        mock_backtester_instance.get_backtest_summary.return_value = {
            "metric_id": unique_summary_metric
        }

        unique_stress_metric = uuid.uuid4().hex
        mock_pipeline_cls.return_value.execute.return_value = {
            "stress_id": unique_stress_metric
        }

        runner = MarketPortfolioStressBacktestRunner(self.random_filepath)
        report = runner.run_stress_backtest(
            symbol=self.random_symbol,
            initial_capital=self.random_capital,
            strategy_params=self.strategy_params,
            percentage=self.random_percentage,
            shifts=self.random_shifts
        )

        self.assertEqual(report["backtest_summary"]["metric_id"], unique_summary_metric)
        self.assertEqual(report["stress_scenario_result"]["stress_id"], unique_stress_metric)
        self.assertEqual(report["symbol"], self.random_symbol)

if __name__ == '__main__':
    unittest.main()