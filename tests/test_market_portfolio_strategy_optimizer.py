import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os

from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer


class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_validate_allocation_valid_float(self):
        val = round(random.uniform(0.0, 1.0), 4)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, val)

    def test_validate_allocation_negative(self):
        val = -abs(random.uniform(0.1, 100.0))
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 0.0)

    def test_validate_allocation_overflow(self):
        val = 1.0 + random.uniform(0.01, 100.0)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 1.0)

    def test_validate_allocation_string_convertible(self):
        val = round(random.uniform(0.0, 1.0), 2)
        result = self.optimizer._validate_allocation(str(val))
        self.assertEqual(result, float(val))

    def test_validate_allocation_invalid_string(self):
        invalid_str = uuid.uuid4().hex
        result = self.optimizer._validate_allocation(invalid_str)
        self.assertEqual(result, 0.0)

    def test_optimize_strategy_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        percentage = round(random.uniform(-50.0, 50.0), 2)

        backtest_data = {uuid.uuid4().hex: random.randint(100, 500)}
        sim_data = {uuid.uuid4().hex: random.uniform(10.0, 99.9)}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=backtest_data) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=sim_data) as mock_sim:

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            mock_bt.assert_called_once_with(symbol, shifts)
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(result['backtest'], backtest_data)
            self.assertEqual(result['simulation'], sim_data)

    def test_optimize_strategy_key_error_handling(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = random.randint(1, 5)
        percentage = round(random.uniform(1.0, 10.0), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError), \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError):

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            self.assertEqual(result, {
                'backtest': {},
                'simulation': {}
            })

    def test_evaluate_resilience_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = [random.randint(1, 3)]
        stress_payload = {uuid.uuid4().hex: random.random()}
        drawdown_val = round(random.uniform(0.0, 1.0), 4)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=stress_payload) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            mock_stress.assert_called_once_with(symbol, shifts)
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(result['stress_data'], stress_payload)
            self.assertEqual(result['drawdown_checked'], drawdown_val)

    def test_evaluate_resilience_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = random.randint(1, 5)

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception):

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        filepath = f"{uuid.uuid4().hex}.bin"
        random_bytes = uuid.uuid4().bytes + os.urandom(16)

        mock_file = io.BytesIO(random_bytes)
        with patch("builtins.open", return_value=mock_file) as mock_open:
            data = self.optimizer.load_strategy_stream(filepath)
            mock_open.assert_called_once_with(filepath, 'rb')
            self.assertEqual(data, random_bytes)

    def test_optimize_and_evaluate_scalar_shift(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation = round(random.uniform(0.0, 1.0), 2)
        shift_val = random.randint(1, 100)

        bt_res = {uuid.uuid4().hex: random.randint(1, 50)}
        stress_res = {uuid.uuid4().hex: random.randint(51, 100)}
        drawdown_val = round(random.uniform(0.0, 0.5), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=bt_res) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=stress_res) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shift_val)

            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_stress.assert_called_once_with(symbol, [shift_val])
            mock_dd.assert_called_once_with(symbol)

            self.assertEqual(result["optimized_weights"], {symbol: allocation})
            self.assertEqual(result["resilience_score"], 1.0 - abs(drawdown_val))
            self.assertEqual(result["backtest"], bt_res)
            self.assertEqual(result["stress"], stress_res)

    def test_optimize_and_evaluate_iterable_shifts_and_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation = round(random.uniform(1.5, 5.0), 2) # Should be validated to 1.0
        shifts_list = [random.randint(1, 10), random.randint(11, 20)]

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError), \
             patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception):

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts_list)

            self.assertEqual(result["optimized_weights"], {symbol: 1.0})
            self.assertEqual(result["resilience_score"], 0.5)
            self.assertEqual(result["backtest"], {})
            self.assertEqual(result["stress"], {})
            self.assertEqual(result["drawdown"], 0.0) if "drawdown" in result else None

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


if __name__ == '__main__':
    unittest.main()