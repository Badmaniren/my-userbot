import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_backtest_runner_v2 import StressBacktestRunnerV2
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine


class TestStressBacktestRunnerV2(unittest.TestCase):

    def setUp(self):
        self.rand_filepath = f"data_{uuid.uuid4().hex}.csv"
        self.rand_portfolio_id = uuid.uuid4().hex
        self.rand_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.rand_capital = random.uniform(10000.0, 1000000.0)
        self.rand_confidence = random.uniform(0.90, 0.99)
        self.rand_horizon = random.randint(1, 30)
        self.rand_simulations = random.randint(100, 5000)

        self.runner = StressBacktestRunnerV2(
            filepath=self.rand_filepath,
            db_storage=MagicMock(),
            extractor_tool=MagicMock(),
            market_anomaly_detector=MagicMock()
        )

    def test_initialization_composition(self):
        self.assertIsInstance(self.runner.backtester, MarketPortfolioBacktester)
        self.assertIsInstance(self.runner.var_engine, PredictiveVarEngine)
        self.assertEqual(self.runner.filepath, self.rand_filepath)

    def test_run_end_to_end_stress_simulation(self):
        mock_equity_data = [self.rand_capital * (1 + random.uniform(-0.05, 0.05)) for _ in range(20)]
        mock_summary = {
            "symbol": self.rand_symbol,
            "initial_capital": self.rand_capital,
            "final_equity": mock_equity_data[-1],
            "max_drawdown": random.uniform(0.01, 0.25)
        }
        mock_var_value = random.uniform(1000.0, 50000.0)

        with patch.object(MarketPortfolioBacktester, "load_data") as mock_load, \
             patch.object(MarketPortfolioBacktester, "run_backtest", return_value=mock_equity_data) as mock_backtest, \
             patch.object(MarketPortfolioBacktester, "get_backtest_summary", return_value=mock_summary) as mock_summary_call, \
             patch.object(PredictiveVarEngine, "calculate_predictive_stress_var", return_value=mock_var_value) as mock_stress_var:

            strategy_params = {"threshold": random.uniform(0.1, 0.9)}
            scenario_params = {"shock": random.uniform(0.05, 0.5)}

            result = self.runner.run_pipeline_simulation(
                symbol=self.rand_symbol,
                portfolio_id=self.rand_portfolio_id,
                strategy_params=strategy_params,
                scenario_params=scenario_params,
                confidence_level=self.rand_confidence,
                horizon_days=self.rand_horizon,
                iterations=self.rand_simulations,
                initial_capital=self.rand_capital
            )

            mock_load.assert_called_once_with(self.rand_filepath)
            mock_backtest.assert_called_once_with(self.rand_symbol, self.rand_capital, strategy_params)
            mock_summary_call.assert_called_once_with(self.rand_symbol)
            mock_stress_var.assert_called_once()

            self.assertEqual(result["symbol"], self.rand_symbol)
            self.assertEqual(result["backtest_summary"], mock_summary)
            self.assertEqual(result["predictive_stress_var"], mock_var_value)
            self.assertIn("simulation_id", result)

    def test_run_pipeline_with_stream_integration(self):
        rand_stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream_mock = io.BytesIO(rand_stream_data)

        with patch.object(PredictiveVarEngine, "process_market_stream", return_value=True) as mock_process_stream:
            execution_status = self.runner.execute_stream_stress_validation(mock_stream_mock)

            mock_process_stream.assert_called_once_with(mock_stream_mock)
            self.assertTrue(execution_status)

    def test_error_propagation_no_silencing(self):
        rand_error_msg = f"Critical failure {uuid.uuid4().hex}"

        with patch.object(MarketPortfolioBacktester, "load_data", side_effect=FileNotFoundError(rand_error_msg)):
            with self.assertRaises(FileNotFoundError) as ctx:
                self.runner.run_pipeline_simulation(
                    symbol=self.rand_symbol,
                    portfolio_id=self.rand_portfolio_id,
                    strategy_params={},
                    scenario_params={},
                    confidence_level=self.rand_confidence,
                    horizon_days=self.rand_horizon,
                    iterations=self.rand_simulations
                )
            self.assertIn(rand_error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()