import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestMarketPortfolioStrategyOptimizer(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_init_attributes(self):
        self.assertEqual(self.optimizer.storage_file, self.storage_file)
        self.assertIsNotNone(self.optimizer.backtester)
        self.assertIsNotNone(self.optimizer.simulator)
        self.assertIsNotNone(self.optimizer.tax_calculator)
        self.assertIsNotNone(self.optimizer.dividend_tracker)

    def test_optimize_strategy_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        percentage = round(random.uniform(0.1, 0.9), 2)

        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_sim = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_backtest) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=expected_sim) as mock_sim:

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            mock_bt.assert_called_once_with(symbol, shifts)
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['simulation'], expected_sim)

    def test_optimize_strategy_key_error(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = random.randint(1, 5)
        percentage = round(random.uniform(0.01, 0.5), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError) as mock_sim:

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            self.assertEqual(result, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [random.randint(1, 10)]
        expected_stress = {uuid.uuid4().hex: random.randint(100, 500)}
        expected_drawdown = round(random.uniform(-0.5, -0.1), 2)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=expected_drawdown) as mock_dd:

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            mock_stress.assert_called_once_with(symbol, shifts)
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(result['stress_data'], expected_stress)
            self.assertEqual(result['drawdown_checked'], expected_drawdown)

    def test_evaluate_resilience_string_drawdown(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = random.randint(1, 5)
        raw_drawdown = round(random.uniform(-0.8, -0.2), 2)
        string_drawdown = str(raw_drawdown)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value={}) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=string_drawdown) as mock_dd:

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            self.assertEqual(result['drawdown_checked'], float(string_drawdown))

    def test_evaluate_resilience_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = random.randint(1, 5)

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception) as mock_dd:

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        filepath = f"{uuid.uuid4().hex}.bin"
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')

        mock_file = io.BytesIO(random_bytes)
        with patch('builtins.open', return_value=mock_file) as mock_open:
            data = self.optimizer.load_strategy_stream(filepath)
            mock_open.assert_called_once_with(filepath, 'rb')
            self.assertEqual(data, random_bytes)

    def test_optimize_and_evaluate_scalar_shift(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        allocation = round(random.uniform(0.1, 1.0), 2)
        shift_val = random.randint(1, 10)
        expected_bt = {uuid.uuid4().hex: random.random()}
        expected_stress = {uuid.uuid4().hex: random.random()}
        drawdown_val = round(random.uniform(-0.4, 0.0), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=expected_bt) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=expected_stress) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shift_val)

            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_stress.assert_called_once_with(symbol, [shift_val])
            self.assertEqual(result['optimized_weights'], {symbol: allocation})
            self.assertEqual(result['resilience_score'], 1.0 - abs(drawdown_val))
            self.assertEqual(result['backtest'], expected_bt)
            self.assertEqual(result['stress'], expected_stress)

    def test_optimize_and_evaluate_iterable_shifts_and_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        allocation = round(random.uniform(0.1, 1.0), 2)
        shift_list = [random.randint(1, 5), random.randint(6, 10)]

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shift_list)

            mock_bt.assert_called_once_with(symbol, shift_list)
            mock_stress.assert_called_once_with(symbol, shift_list)
            self.assertEqual(result['optimized_weights'], {symbol: allocation})
            self.assertEqual(result['resilience_score'], 0.5)
            self.assertEqual(result['backtest'], {})
            self.assertEqual(result['stress'], {})

    def test_get_strategy_summary(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        summary = self.optimizer.get_strategy_summary(symbol)

        expected = {
            symbol: {
                "summary": "active",
                "storage": self.storage_file
            }
        }
        self.assertEqual(summary, expected)