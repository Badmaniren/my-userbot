import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_path = f"{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_path)

    def test_init_state(self):
        self.assertEqual(self.optimizer.storage_file, self.storage_path)
        self.assertIsNotNone(self.optimizer.backtester)
        self.assertIsNotNone(self.optimizer.simulator)

    def test_validate_allocation_valid_floats(self):
        valid_val = round(random.uniform(0.0, 1.0), 4)
        result = self.optimizer._validate_allocation(valid_val)
        self.assertIsInstance(result, float)
        self.assertEqual(result, valid_val)

    def test_validate_allocation_boundary_conditions(self):
        below_zero = -round(random.uniform(0.1, 10.0), 2)
        self.assertEqual(self.optimizer._validate_allocation(below_zero), 0.0)

        above_one = 1.0 + round(random.uniform(0.1, 10.0), 2)
        self.assertEqual(self.optimizer._validate_allocation(above_one), 1.0)

    def test_validate_allocation_string_parsing(self):
        target_val = round(random.uniform(0.0, 1.0), 2)
        result = self.optimizer._validate_allocation(str(target_val))
        self.assertEqual(result, float(target_val))

    def test_validate_allocation_invalid_types(self):
        garbage_input = uuid.uuid4().hex
        result = self.optimizer._validate_allocation(garbage_input)
        self.assertEqual(result, 0.0)

    def test_optimize_strategy_success(self):
        shifts = [random.randint(1, 30) for _ in range(3)]
        percentage = round(random.uniform(1.0, 50.0), 2)
        backtest_mock_data = {uuid.uuid4().hex: random.random()}
        simulation_mock_data = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=backtest_mock_data) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=simulation_mock_data) as mock_sim:
            
            res = self.optimizer.optimize_strategy(self.symbol, shifts, percentage)
            
            mock_bt.assert_called_once_with(self.symbol, shifts)
            mock_sim.assert_called_once_with(self.symbol, percentage)
            self.assertEqual(res['backtest'], backtest_mock_data)
            self.assertEqual(res['simulation'], simulation_mock_data)

    def test_optimize_strategy_key_error_handling(self):
        shifts = random.randint(1, 10)
        percentage = round(random.uniform(1.0, 100.0), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError) as mock_sim:
            
            res = self.optimizer.optimize_strategy(self.symbol, shifts, percentage)
            
            self.assertEqual(res, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_success(self):
        shifts = [random.randint(5, 50) for _ in range(2)]
        stress_mock = {uuid.uuid4().hex: uuid.uuid4().hex}
        drawdown_val = -round(random.uniform(0.01, 0.99), 2)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=stress_mock) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(self.symbol, shifts)

            mock_stress.assert_called_once_with(self.symbol, shifts)
            mock_dd.assert_called_once_with(self.symbol)
            self.assertEqual(res['stress_data'], stress_mock)
            self.assertEqual(res['drawdown_checked'], drawdown_val)

    def test_evaluate_resilience_drawdown_string_conversion(self):
        shifts = random.randint(1, 10)
        stress_mock = {}
        drawdown_str = str(round(random.uniform(-0.8, -0.1), 2))

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=stress_mock), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_str):
            
            res = self.optimizer.evaluate_resilience(self.symbol, shifts)
            self.assertIsInstance(res['drawdown_checked'], float)
            self.assertEqual(res['drawdown_checked'], float(drawdown_str))

    def test_evaluate_resilience_exceptions_fallback(self):
        shifts = random.randint(1, 5)

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception):
            
            res = self.optimizer.evaluate_resilience(self.symbol, shifts)
            self.assertEqual(res['stress_data'], {})
            self.assertEqual(res['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        filepath = f"{uuid.uuid4().hex}.bin"
        random_bytes = uuid.uuid4().bytes + b"".join(bytes([random.randint(0, 255)]) for _ in range(16))
        mock_file = io.BytesIO(random_bytes)

        with patch("builtins.open", return_value=mock_file) as mock_open:
            result = self.optimizer.load_strategy_stream(filepath)
            mock_open.assert_called_once_with(filepath, 'rb')
            self.assertEqual(result, random_bytes)

    def test_optimize_and_evaluate_workflow(self):
        allocation_input = round(random.uniform(0.0, 1.0), 2)
        shifts = [random.randint(10, 100)]
        backtest_res_mock = {uuid.uuid4().hex: random.randint(1, 100)}
        stress_res_mock = {uuid.uuid4().hex: random.randint(100, 200)}
        drawdown_val = -0.25

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=backtest_res_mock) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=stress_res_mock) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            res = self.optimizer.optimize_and_evaluate(self.symbol, allocation_input, shifts)

            mock_bt.assert_called_once_with(self.symbol, shifts)
            mock_stress.assert_called_once_with(self.symbol, shifts)
            mock_dd.assert_called_once_with(self.symbol)

            self.assertEqual(res['optimized_weights'], {self.symbol: allocation_input})
            self.assertEqual(res['resilience_score'], 1.0 - abs(drawdown_val))
            self.assertEqual(res['backtest'], backtest_res_mock)
            self.assertEqual(res['stress'], stress_res_mock)

    def test_optimize_and_evaluate_scalar_shifts(self):
        allocation_input = round(random.uniform(0.0, 1.0), 2)
        scalar_shift = random.randint(1, 50)
        
        with patch.object(self.optimizer.backtester, 'run_backtest', return_value={}) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value={}) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=0.0):
            
            self.optimizer.optimize_and_evaluate(self.symbol, allocation_input, scalar_shift)
            mock_bt.assert_called_once_with(self.symbol, [scalar_shift])
            mock_stress.assert_called_once_with(self.symbol, [scalar_shift])

    def test_get_strategy_summary(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["summary"], "active")
        self.assertEqual(summary[self.symbol]["storage"], self.storage_path)

if __name__ == '__main__':
    unittest.main()