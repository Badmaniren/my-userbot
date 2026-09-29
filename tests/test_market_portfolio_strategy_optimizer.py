import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(storage_file=self.storage_file)

    def test_validate_allocation_valid(self):
        val = round(random.uniform(0.0, 1.0), 4)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, float(val))

    def test_validate_allocation_string_conversion(self):
        val = round(random.uniform(0.0, 1.0), 4)
        result = self.optimizer._validate_allocation(str(val))
        self.assertEqual(result, float(val))

    def test_validate_allocation_out_of_bounds_high(self):
        val = random.uniform(1.0001, 10.0)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 1.0)

    def test_validate_allocation_out_of_bounds_low(self):
        val = random.uniform(-10.0, -0.0001)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 0.0)

    def test_validate_allocation_invalid_type(self):
        invalid_val = uuid.uuid4().hex
        result = self.optimizer._validate_allocation(invalid_val)
        self.assertEqual(result, 0.0)

    def test_optimize_strategy_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift = random.randint(1, 100)
        percentage = round(random.uniform(1.0, 50.0), 2)
        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_simulation = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_backtest) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=expected_simulation) as mock_sim:
            
            res = self.optimizer.optimize_strategy(symbol, shift, percentage)
            mock_bt.assert_called_once_with(symbol, [shift])
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res['backtest'], expected_backtest)
            self.assertEqual(res['simulation'], expected_simulation)

    def test_optimize_strategy_keyerror_handling(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        percentage = round(random.uniform(1.0, 10.0), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError) as mock_sim:
            
            res = self.optimizer.optimize_strategy(symbol, shifts, percentage)
            mock_bt.assert_called_once_with(symbol, shifts)
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res['backtest'], {})
            self.assertEqual(res['simulation'], {})

    def evaluate_resilience_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift = random.uniform(0.1, 5.0)
        expected_stress = {uuid.uuid4().hex: random.randint(100, 500)}
        expected_drawdown = -round(random.uniform(0.01, 0.5), 4)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=expected_drawdown) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(symbol, shift)
            mock_stress.assert_called_once_with(symbol, [shift])
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(res['stress_data'], expected_stress)
            self.assertEqual(res['drawdown_checked'], expected_drawdown)

    def test_load_strategy_stream(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        fake_filepath = f"{uuid.uuid4().hex}.bin"
        mock_file = io.BytesIO(random_bytes)

        with patch('builtins.open', return_value=mock_file) as mock_open:
            data = self.optimizer.load_strategy_stream(fake_filepath)
            mock_open.assert_called_once_with(fake_filepath, 'rb')
            self.assertEqual(data, random_bytes)

    def test_optimize_and_evaluate_normal(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation = round(random.uniform(0.1, 0.9), 2)
        shift = random.randint(5, 50)
        expected_bt = {uuid.uuid4().hex: random.random()}
        expected_stress = {uuid.uuid4().hex: random.random()}
        drawdown_val = -round(random.uniform(0.1, 0.4), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_bt) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            res = self.optimizer.optimize_and_evaluate(symbol, allocation, shift)
            self.assertEqual(res['optimized_weights'], {symbol: allocation})
            self.assertEqual(res['resilience_score'], 1.0 - abs(drawdown_val))
            self.assertEqual(res['backtest'], expected_bt)
            self.assertEqual(res['stress'], expected_stress)

    def test_get_strategy_summary(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        summary = self.optimizer.get_strategy_summary(symbol)
        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_file)

if __name__ == '__main__':
    unittest.main()