import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer


class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        with patch("skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester"), \
             patch("skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator"):
            self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_validate_allocation_valid_ranges(self):
        val_float = round(random.uniform(0.0, 1.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(val_float), val_float)

        val_int = random.choice([0, 1])
        self.assertEqual(self.optimizer._validate_allocation(val_int), float(val_int))

        val_str = str(round(random.uniform(0.0, 1.0), 4))
        self.assertEqual(self.optimizer._validate_allocation(val_str), float(val_str))

    def test_validate_allocation_boundary_conditions(self):
        below_zero = -abs(random.uniform(0.1, 100.0))
        self.assertEqual(self.optimizer._validate_allocation(below_zero), 0.0)

        above_one = 1.0 + abs(random.uniform(0.1, 100.0))
        self.assertEqual(self.optimizer._validate_allocation(above_one), 1.0)

        invalid_type = f"invalid_{uuid.uuid4().hex}"
        self.assertEqual(self.optimizer._validate_allocation(invalid_type), 0.0)

    def test_optimize_strategy_with_single_shift_and_iterable(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = random.randint(1, 50)
        percentage = round(random.uniform(1.0, 99.9), 2)

        mock_backtest = {uuid.uuid4().hex: random.random()}
        mock_simulation = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=mock_backtest) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=mock_simulation) as mock_sim:
            
            result = self.optimizer.optimize_strategy(symbol, shift_val, percentage)

            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(result['backtest'], mock_backtest)
            self.assertEqual(result['simulation'], mock_simulation)

    def test_optimize_strategy_key_error_handling(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        percentage = round(random.uniform(1.0, 99.9), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError), \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError):
            
            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)
            self.assertEqual(result, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_comprehensive(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shift_val = random.randint(1, 100)
        mock_stress = {uuid.uuid4().hex: random.randint(100, 500)}
        drawdown_val = round(random.uniform(-0.9, -0.1), 2)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=mock_stress) as mock_st, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            result = self.optimizer.evaluate_resilience(symbol, shift_val)

            mock_st.assert_called_once_with(symbol, [shift_val])
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(result['stress_data'], mock_stress)
            self.assertEqual(result['drawdown_checked'], drawdown_val)

    def test_evaluate_resilience_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        shifts = (random.randint(1, 5), random.randint(6, 10))

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception):
            
            result = self.optimizer.evaluate_resilience(symbol, shifts)
            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        filepath = f"file_{uuid.uuid4().hex}.bin"
        random_bytes = bytes(random.getrandbits(8) for _ in range(32))

        mock_file = io.BytesIO(random_bytes)
        with patch("builtins.open", return_value=mock_file):
            stream_data = self.optimizer.load_strategy_stream(filepath)
            self.assertEqual(stream_data, random_bytes)

    def test_optimize_and_evaluate_comprehensive(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation = round(random.uniform(0.0, 1.0), 2)
        shift_val = random.randint(1, 20)

        mock_backtest_res = {uuid.uuid4().hex: random.random()}
        mock_stress_res = {uuid.uuid4().hex: random.random()}
        drawdown_val = round(random.uniform(-0.5, 0.0), 2)

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=mock_backtest_res) as mock_bt, \
             patch.object(self.optimizer.simulator, 'run_stress_test', return_value=mock_stress_res) as mock_st, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shift_val)

            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_st.assert_called_once_with(symbol, [shift_val])
            mock_dd.assert_called_once_with(symbol)

            expected_weights = {symbol: allocation}
            expected_resilience = 1.0 - abs(drawdown_val)

            self.assertEqual(result['optimized_weights'], expected_weights)
            self.assertEqual(result['resilience_score'], expected_resilience)
            self.assertEqual(result['backtest'], mock_backtest_res)
            self.assertEqual(result['stress'], mock_stress_res)

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