import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_path = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_path)

    def test_validate_allocation_boundary_and_types(self):
        rand_valid = round(random.uniform(0.0, 1.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(rand_valid), float(rand_valid))
        
        self.assertEqual(self.optimizer._validate_allocation(-1.5 * random.random()), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(1.0 + random.random()), 1.0)
        
        str_val = str(round(random.uniform(0.1, 0.9), 2))
        self.assertEqual(self.optimizer._validate_allocation(str_val), float(str_val))
        
        rand_garbage = uuid.uuid4().hex
        self.assertEqual(self.optimizer._validate_allocation(rand_garbage), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(None), 0.0)

    def test_optimize_strategy_success(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shift_val = random.randint(1, 100)
        percentage_val = random.random()

        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_simulation = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_backtest) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=expected_simulation) as mock_sim:
            
            result = self.optimizer.optimize_strategy(symbol, shift_val, percentage_val)
            
            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_sim.assert_called_once_with(symbol, percentage_val)
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['simulation'], expected_simulation)

    def test_optimize_strategy_key_error_handling(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts_list = [random.randint(1, 50), random.randint(51, 100)]
        percentage_val = random.random()

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError), \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError):
            
            result = self.optimizer.optimize_strategy(symbol, shifts_list, percentage_val)
            
            self.assertEqual(result, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_success(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shift_val = random.randint(5, 50)
        expected_stress = {uuid.uuid4().hex: random.randint(100, 500)}
        expected_drawdown = -round(random.uniform(0.01, 0.5), 2)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=expected_drawdown) as mock_dd:
            
            result = self.optimizer.evaluate_resilience(symbol, shift_val)
            
            mock_stress.assert_called_once_with(symbol, [shift_val])
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(result['stress_data'], expected_stress)
            self.assertEqual(result['drawdown_checked'], float(expected_drawdown))

    def test_evaluate_resilience_exception_handling(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shift_val = random.randint(1, 10)

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception):
            
            result = self.optimizer.evaluate_resilience(symbol, shift_val)
            
            self.assertEqual(result, {'stress_data': {}, 'drawdown_checked': 0.0})

    def test_load_strategy_stream(self):
        random_bytes = uuid.uuid4().bytes + random.randbytes(16)
        filepath = f"{uuid.uuid4().hex}.bin"

        mock_file = io.BytesIO(random_bytes)
        with patch('builtins.open', return_value=mock_file) as mock_open:
            stream_data = self.optimizer.load_strategy_stream(filepath)
            mock_open.assert_called_once_with(filepath, 'rb')
            self.assertEqual(stream_data, random_bytes)

    def test_optimize_and_evaluate_success(self):
        symbol = uuid.uuid4().hex[:6].upper()
        allocation_val = round(random.uniform(0.1, 0.9), 2)
        shifts = [random.randint(1, 10)]

        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_stress = {uuid.uuid4().hex: random.random()}
        drawdown_str = str(-round(random.uniform(0.1, 0.4), 2))

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_backtest), \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_str):
            
            result = self.optimizer.optimize_and_evaluate(symbol, allocation_val, shifts)
            
            self.assertEqual(result['optimized_weights'], {symbol: allocation_val})
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['stress'], expected_stress)
            self.assertIn('resilience_score', result)
            self.assertIsInstance(result['resilience_score'], float)

    def test_get_strategy_summary(self):
        symbol = uuid.uuid4().hex[:6].upper()
        summary = self.optimizer.get_strategy_summary(symbol)
        
        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_path)