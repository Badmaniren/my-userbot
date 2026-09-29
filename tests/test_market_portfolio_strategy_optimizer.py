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

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_validate_allocation_boundaries_and_types(self):
        valid_val = round(random.uniform(0.0, 1.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(valid_val), valid_val)

        over_val = round(random.uniform(1.1, 100.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(over_val), 1.0)

        under_val = round(random.uniform(-100.0, -0.1), 4)
        self.assertEqual(self.optimizer._validate_allocation(under_val), 0.0)

        str_val = str(round(random.uniform(0.0, 1.0), 4))
        self.assertEqual(self.optimizer._validate_allocation(str_val), float(str_val))

        chaos_str = f"{uuid.uuid4().hex}"
        self.assertEqual(self.optimizer._validate_allocation(chaos_str), 0.0)

        self.assertEqual(self.optimizer._validate_allocation(None), 0.0)

    def test_optimize_strategy_with_iterables_and_scalars(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = random.randint(1, 10)
        percentage = round(random.uniform(0.01, 0.99), 4)
        
        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_sim = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_backtest) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=expected_sim) as mock_sim:
            
            res = self.optimizer.optimize_strategy(symbol, shift_val, percentage)
            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res['backtest'], expected_backtest)
            self.assertEqual(res['simulation'], expected_sim)

    def test_optimize_strategy_key_error_handling(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = [random.randint(1, 5) for _ in range(3)]
        percentage = round(random.uniform(0.0, 1.0), 4)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError) as mock_sim:
            
            res = self.optimizer.optimize_strategy(symbol, shifts, percentage)
            mock_bt.assert_called_once_with(symbol, shifts)
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_success_and_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = round(random.uniform(1.0, 10.0), 2)
        
        stress_payload = {uuid.uuid4().hex: random.randint(100, 500)}
        drawdown_str = str(round(random.uniform(-0.5, -0.1), 2))

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=stress_payload) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_str) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(symbol, shift_val)
            mock_stress.assert_called_once_with(symbol, [shift_val])
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(res['stress_data'], stress_payload)
            self.assertEqual(res['drawdown_checked'], float(drawdown_str))

    def test_evaluate_resilience_fallback_on_failure(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = (random.randint(1, 3), random.randint(4, 6))

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(symbol, shifts)
            mock_stress.assert_called_once_with(symbol, list(shifts))
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(res, {'stress_data': {}, 'drawdown_checked': 0.0})

    def test_load_strategy_stream_binary_read(self):
        random_bytes = uuid.uuid4().bytes + os.urandom(16)
        filepath = f"{uuid.uuid4().hex}.bin"

        mock_file = io.BytesIO(random_bytes)
        
        with patch('builtins.open', return_value=mock_file) as mock_op:
            stream_data = self.optimizer.load_strategy_stream(filepath)
            mock_op.assert_called_once_with(filepath, 'rb')
            self.assertEqual(stream_data, random_bytes)

    def test_optimize_and_evaluate_comprehensive(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation_input = round(random.uniform(1.5, 5.0), 2)
        shifts = [random.randint(1, 10)]

        expected_bt = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_stress = {uuid.uuid4().hex: uuid.uuid4().hex}
        drawdown_val = round(random.uniform(-0.3, -0.1), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_bt) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            result = self.optimizer.optimize_and_evaluate(symbol, allocation_input, shifts)
            
            mock_bt.assert_called_once_with(symbol, shifts)
            mock_stress.assert_called_once_with(symbol, shifts)
            mock_dd.assert_called_once_with(symbol)

            self.assertEqual(result['optimized_weights'], {symbol: 1.0})
            self.assertEqual(result['resilience_score'], 1.0 - abs(drawdown_val))
            self.assertEqual(result['backtest'], expected_bt)
            self.assertEqual(result['stress'], expected_stress)

    def test_get_strategy_summary_structure(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        summary = self.optimizer.get_strategy_summary(symbol)
        
        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_file)