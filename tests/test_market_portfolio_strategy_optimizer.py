import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file_path = f"storage_{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file_path)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_init_and_dependencies(self, mock_simulator_cls, mock_backtester_cls):
        custom_storage = f"custom_store_{uuid.uuid4().hex}.dat"
        optimizer = PortfolioStrategyOptimizer(custom_storage)
        self.assertEqual(optimizer.storage_file, custom_storage)
        mock_backtester_cls.assert_called_once_with(custom_storage)
        mock_simulator_cls.assert_called_once_with(custom_storage)

    def test_validate_allocation_boundaries_and_types(self):
        valid_val = round(random.uniform(0.0, 1.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(valid_val), valid_val)

        overflow_val = 1.0 + random.uniform(0.1, 10.0)
        self.assertEqual(self.optimizer._validate_allocation(overflow_val), 1.0)

        underflow_val = -1.0 * random.uniform(0.1, 10.0)
        self.assertEqual(self.optimizer._validate_allocation(underflow_val), 0.0)

        string_val = str(round(random.uniform(0.0, 1.0), 2))
        self.assertEqual(self.optimizer._validate_allocation(string_val), float(string_val))

        invalid_string = f"not_a_number_{uuid.uuid4().hex}"
        self.assertEqual(self.optimizer._validate_allocation(invalid_string), 0.0)

        self.assertEqual(self.optimizer._validate_allocation(None), 0.0)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_optimize_strategy_success(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = random.randint(1, 100)
        percentage_val = random.uniform(1.0, 50.0)

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_simulation = {uuid.uuid4().hex: random.random()}

        backtest_mock_instance.run_backtest.return_value = expected_backtest
        simulator_mock_instance.simulate_scenario.return_value = expected_simulation

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.optimize_strategy(symbol, shift_val, percentage_val)

        backtest_mock_instance.run_backtest.assert_called_once_with(symbol, [shift_val])
        simulator_mock_instance.simulate_scenario.assert_called_once_with(symbol, percentage_val)

        self.assertEqual(result['backtest'], expected_backtest)
        self.assertEqual(result['simulation'], expected_simulation)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_optimize_strategy_key_error_handling(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts_list = [random.randint(1, 50), random.randint(51, 100)]
        percentage_val = random.uniform(0.5, 10.0)

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        backtest_mock_instance.run_backtest.side_effect = KeyError("Missing backtest data")
        simulator_mock_instance.simulate_scenario.side_effect = KeyError("Missing simulation data")

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.optimize_strategy(symbol, shifts_list, percentage_val)

        backtest_mock_instance.run_backtest.assert_called_once_with(symbol, shifts_list)
        simulator_mock_instance.simulate_scenario.assert_called_once_with(symbol, percentage_val)

        self.assertEqual(result, {'backtest': {}, 'simulation': {}})

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_evaluate_resilience_success(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = random.randint(1, 20)

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        expected_stress = {uuid.uuid4().hex: random.uniform(10, 100)}
        drawdown_val = round(random.uniform(-0.5, 0.0), 2)

        simulator_mock_instance.run_stress_test.return_value = expected_stress
        backtest_mock_instance.calculate_maximum_drawdown.return_value = drawdown_val

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.evaluate_resilience(symbol, shift_val)

        simulator_mock_instance.run_stress_test.assert_called_once_with(symbol, [shift_val])
        backtest_mock_instance.calculate_maximum_drawdown.assert_called_once_with(symbol)

        self.assertEqual(result['stress_data'], expected_stress)
        self.assertEqual(result['drawdown_checked'], drawdown_val)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_evaluate_resilience_exceptions(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = [random.randint(1, 10)]

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        simulator_mock_instance.run_stress_test.side_effect = KeyError("No stress test")
        backtest_mock_instance.calculate_maximum_drawdown.side_effect = Exception("Drawdown failure")

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.evaluate_resilience(symbol, shifts)

        self.assertEqual(result['stress_data'], {})
        self.assertEqual(result['drawdown_checked'], 0.0)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_evaluate_resilience_string_drawdown(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = random.randint(1, 10)
        drawdown_str = str(round(random.uniform(-1.0, 0.0), 3))

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        simulator_mock_instance.run_stress_test.return_value = {}
        backtest_mock_instance.calculate_maximum_drawdown.return_value = drawdown_str

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.evaluate_resilience(symbol, shift_val)

        self.assertEqual(result['drawdown_checked'], float(drawdown_str))

    def test_load_strategy_stream(self):
        random_bytes = uuid.uuid4().bytes + os_random_bytes_helper()
        filepath = f"strategy_{uuid.uuid4().hex}.bin"

        mock_file = io.BytesIO(random_bytes)
        with patch("builtins.open", return_value=mock_file) as mock_open:
            stream_data = self.optimizer.load_strategy_stream(filepath)
            mock_open.assert_called_once_with(filepath, 'rb')
            self.assertEqual(stream_data, random_bytes)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_optimize_and_evaluate_success(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation_val = round(random.uniform(0.1, 0.9), 2)
        shift_val = random.randint(1, 10)

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        backtest_res = {uuid.uuid4().hex: random.random()}
        stress_res = {uuid.uuid4().hex: random.random()}
        drawdown_val = -0.25

        backtest_mock_instance.run_backtest.return_value = backtest_res
        simulator_mock_instance.run_stress_test.return_value = stress_res
        backtest_mock_instance.calculate_maximum_drawdown.return_value = drawdown_val

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.optimize_and_evaluate(symbol, allocation_val, shift_val)

        self.assertEqual(result["optimized_weights"], {symbol: allocation_val})
        self.assertEqual(result["resilience_score"], 1.0 - abs(drawdown_val))
        self.assertEqual(result["backtest"], backtest_res)
        self.assertEqual(result["stress"], stress_res)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_optimize_and_evaluate_exceptions_fallback(self, mock_simulator_cls, mock_backtester_cls):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation_val = random.uniform(1.5, 5.0)
        shifts = [random.randint(1, 5)]

        backtest_mock_instance = mock_backtester_cls.return_value
        simulator_mock_instance = mock_simulator_cls.return_value

        backtest_mock_instance.run_backtest.side_effect = KeyError("No backtest")
        simulator_mock_instance.run_stress_test.side_effect = KeyError("No stress")
        backtest_mock_instance.calculate_maximum_drawdown.side_effect = Exception("Critical fail")

        optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        result = optimizer.optimize_and_evaluate(symbol, allocation_val, shifts)

        self.assertEqual(result["optimized_weights"], {symbol: 1.0})
        self.assertEqual(result["resilience_score"], 0.5)
        self.assertEqual(result["backtest"], {})
        self.assertEqual(result["stress"], {})

    def test_get_strategy_summary(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        summary = self.optimizer.get_strategy_summary(symbol)

        expected = {
            symbol: {
                "summary": "active",
                "storage": self.storage_file
            }
        }
        self.assertEqual(summary, expected)


def os_random_bytes_helper():
    return bytes([random.randint(0, 255) for _ in range(16)])

if __name__ == '__main__':
    unittest.main()