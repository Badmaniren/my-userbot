import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_backtest_stress_evaluator import MarketBacktestStressEvaluator


class TestMarketBacktestStressEvaluator(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.filepath = f"file_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)]
        self.strategy_params = {"initial_capital": random.uniform(1000.0, 100000.0)}
        self.percentage = random.uniform(1.0, 15.0)

    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    def test_init_and_paths(self, mock_simulator_cls, mock_backtester_cls):
        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)
        self.assertEqual(evaluator.storage_file, self.storage_file)
        self.assertEqual(evaluator.filepath, self.filepath)
        mock_backtester_cls.assert_called_once_with(self.filepath)
        mock_simulator_cls.assert_called_once_with(self.storage_file)

    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    def test_init_default_filepath(self, mock_simulator_cls, mock_backtester_cls):
        evaluator = MarketBacktestStressEvaluator(self.storage_file)
        self.assertEqual(evaluator.filepath, self.storage_file)
        mock_backtester_cls.assert_called_once_with(self.storage_file)
        mock_simulator_cls.assert_called_once_with(self.storage_file)

    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    def test_evaluate_strategy_stress_and_backtest(self, mock_backtester_cls, mock_simulator_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_simulator_instance = mock_simulator_cls.return_value

        expected_summary = {f"summary_{uuid.uuid4().hex}": random.randint(1, 100)}
        expected_stress = {f"stress_{uuid.uuid4().hex}": random.uniform(1.0, 50.0)}

        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_simulator_instance.run_stress_test.return_value = expected_stress

        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)
        result = evaluator.evaluate_strategy_stress_and_backtest(self.symbol, self.shifts, self.strategy_params)

        mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.shifts, self.strategy_params)
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_simulator_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)

        self.assertIn("backtest_summary", result)
        self.assertIn("stress_test_results", result)
        self.assertEqual(result["backtest_summary"], expected_summary)
        self.assertEqual(result["stress_test_results"], expected_stress)

    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    def test_run_comprehensive_evaluation_stream(self, mock_backtester_cls, mock_simulator_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_simulator_instance = mock_simulator_cls.return_value

        expected_summary = {f"back_{uuid.uuid4().hex}": random.random()}
        expected_simulation = {f"sim_{uuid.uuid4().hex}": random.random()}

        mock_backtester_instance.get_backtest_summary.return_value = expected_summary
        mock_simulator_instance.simulate_scenario.return_value = expected_simulation

        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)
        result = evaluator.run_comprehensive_evaluation_stream(self.symbol, self.shifts, self.strategy_params, self.percentage)

        mock_backtester_instance.run_backtest.assert_called_once_with(self.symbol, self.shifts, self.strategy_params)
        mock_backtester_instance.get_backtest_summary.assert_called_once_with(self.symbol)
        mock_simulator_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)

        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["backtest"], expected_summary)
        self.assertEqual(result["scenario_simulation"], expected_simulation)

    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    def test_evaluate_strategy_stress_success(self, mock_backtester_cls, mock_simulator_cls):
        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)

        expected_summary = {f"sum_{uuid.uuid4().hex}": uuid.uuid4().hex}
        expected_stress = {f"str_{uuid.uuid4().hex}": uuid.uuid4().hex}

        evaluator.backtester.run_backtest = MagicMock(return_value={f"res_{uuid.uuid4().hex}": 123})
        evaluator.backtester.get_backtest_summary = MagicMock(return_value=expected_summary)
        evaluator.simulator.simulate_scenario = MagicMock(return_value=expected_stress)

        capital = random.uniform(500.0, 5000.0)
        shift_val = random.uniform(0.01, 0.5)

        result = evaluator.evaluate_strategy_stress(self.symbol, capital, shift_val)

        evaluator.backtester.run_backtest.assert_called_once_with(
            self.symbol, [shift_val], {"initial_capital": capital}
        )
        evaluator.backtester.get_backtest_summary.assert_called_once_with(self.symbol)
        evaluator.simulator.simulate_scenario.assert_called_once_with(self.symbol, shift_val)

        self.assertEqual(result["backtest"], expected_summary)
        self.assertEqual(result["stress_test"], expected_stress)

    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    def test_evaluate_strategy_stress_fallback_on_exception(self, mock_backtester_cls, mock_simulator_cls):
        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)

        backtest_raw_result = {f"raw_{uuid.uuid4().hex}": random.randint(10, 100)}
        evaluator.backtester.run_backtest = MagicMock(return_value=backtest_raw_result)
        evaluator.backtester.get_backtest_summary = MagicMock(return_value=None)

        evaluator.simulator.simulate_scenario = MagicMock(side_effect=KeyError(self.symbol))

        capital = random.uniform(100.0, 1000.0)
        shift_val = random.uniform(0.1, 0.9)

        result = evaluator.evaluate_strategy_stress(self.symbol, capital, shift_val)

        evaluator.simulator.simulate_scenario.assert_called_once_with(self.symbol, shift_val)
        self.assertEqual(result["backtest"], backtest_raw_result)
        self.assertEqual(result["stress_test"], {"shift": shift_val, "status": "simulated"})

    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    def test_run_comprehensive_evaluation_stream_keyerror_fallback(self, mock_backtester_cls, mock_simulator_cls):
        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)

        expected_summary = {"status": "ready"}
        evaluator.backtester.get_backtest_summary = MagicMock(return_value=expected_summary)
        evaluator.simulator.simulate_scenario = MagicMock(side_effect=KeyError(f"Symbol {self.symbol} not found"))

        result = evaluator.run_comprehensive_evaluation_stream(self.symbol, self.shifts, self.strategy_params, self.percentage)

        evaluator.simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["backtest"], expected_summary)
        self.assertEqual(result["scenario_simulation"], {
            "symbol": self.symbol,
            "simulated_price": 0.0,
            "pnl_impact": 0.0,
            "portfolio_value_delta": 0.0,
            "status": "simulated"
        })

    @patch("skills.market_backtest_stress_evaluator.PortfolioScenarioSimulator")
    @patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester")
    def test_evaluate_strategy_stress_type_error_fallback(self, mock_backtester_cls, mock_simulator_cls):
        evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)

        evaluator.backtester.run_backtest = MagicMock(return_value=None)
        evaluator.backtester.get_backtest_summary = MagicMock(return_value=None)
        evaluator.simulator.simulate_scenario = MagicMock(side_effect=TypeError(uuid.uuid4().hex))

        capital = random.uniform(200.0, 2000.0)
        shift_val = random.uniform(0.05, 0.25)

        result = evaluator.evaluate_strategy_stress(self.symbol, capital, shift_val)

        self.assertIsNone(result["backtest"])
        self.assertEqual(result["stress_test"], {"shift": shift_val, "status": "simulated"})

    def test_stream_bytes_io_mocking_chaos(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        with patch("skills.market_backtest_stress_evaluator.MarketPortfolioBacktester") as mock_bt:
            instance = mock_bt.return_value
            instance.get_backtest_summary.return_value = {"stream_bytes_len": len(random_bytes.read())}

            evaluator = MarketBacktestStressEvaluator(self.storage_file, self.filepath)
            summary = evaluator.backtester.get_backtest_summary(self.symbol)
            self.assertIn("stream_bytes_len", summary)
            self.assertGreater(summary["stream_bytes_len"], 0)