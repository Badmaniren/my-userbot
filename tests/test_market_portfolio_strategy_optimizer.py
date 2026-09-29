import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer


class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.random_storage)

    def test_validate_allocation_valid_floats(self):
        val = round(random.uniform(0.0, 1.0), 4)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, float(val))

    def test_validate_allocation_boundary_conditions(self):
        self.assertEqual(self.optimizer._validate_allocation(-5.5), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(15.5), 1.0)
        self.assertEqual(self.optimizer._validate_allocation(0.0), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(1.0), 1.0)

    def test_validate_allocation_string_conversion(self):
        valid_str = str(round(random.uniform(0.1, 0.9), 2))
        self.assertEqual(self.optimizer._validate_allocation(valid_str), float(valid_str))

        invalid_str = ''.join(random.choices(string.ascii_letters, k=8))
        self.assertEqual(self.optimizer._validate_allocation(invalid_str), 0.0)

    def test_optimize_strategy_with_single_shift(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_shift = random.randint(1, 100)
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        
        expected_backtest = {uuid.uuid4().hex: random.randint(10, 500)}
        expected_simulation = {uuid.uuid4().hex: random.uniform(0.1, 99.9)}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=expected_backtest) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_simulation) as mock_sim:
            
            result = self.optimizer.optimize_strategy(rand_symbol, rand_shift, rand_percentage)
            
            mock_bt.assert_called_once_with(rand_symbol, [rand_shift])
            mock_sim.assert_called_once_with(rand_symbol, rand_percentage)
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['simulation'], expected_simulation)

    def test_optimize_strategy_with_key_errors(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        shifts_list = [random.randint(1, 10), random.randint(11, 20)]
        rand_percentage = round(random.uniform(1.0, 10.0), 2)

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', side_effect=KeyError), \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError):
            
            result = self.optimizer.optimize_strategy(rand_symbol, shifts_list, rand_percentage)
            
            self.assertEqual(result['backtest'], {})
            self.assertEqual(result['simulation'], {})

    def test_evaluate_resilience_success(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        shift_val = random.randint(5, 50)
        expected_stress = {uuid.uuid4().hex: random.uniform(-10.0, 0.0)}
        drawdown_val = round(random.uniform(-0.5, -0.01), 4)

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=expected_stress) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            result = self.optimizer.evaluate_resilience(rand_symbol, shift_val)
            
            mock_stress.assert_called_once_with(rand_symbol, [shift_val])
            mock_dd.assert_called_once_with(rand_symbol)
            self.assertEqual(result['stress_data'], expected_stress)
            self.assertEqual(result['drawdown_checked'], drawdown_val)

    def test_evaluate_resilience_drawdown_string(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        shifts = (random.randint(1, 5), random.randint(6, 10))
        drawdown_str = str(round(random.uniform(-0.9, -0.1), 2))

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError), \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_str):
            
            result = self.optimizer.evaluate_resilience(rand_symbol, shifts)
            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], float(drawdown_str))

    def test_load_strategy_stream(self):
        random_bytes = uuid.uuid4().bytes + b"".join(random.choices([b'a', b'b', b'c'], k=32))
        random_filepath = f"{uuid.uuid4().hex}.bin"

        mock_file = io.BytesIO(random_bytes)
        with patch("builtins.open", return_value=mock_file) as mock_open:
            stream_data = self.optimizer.load_strategy_stream(random_filepath)
            mock_open.assert_called_once_with(random_filepath, 'rb')
            self.assertEqual(stream_data, random_bytes)

    def test_optimize_and_evaluate_comprehensive(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        allocation = round(random.uniform(0.0, 1.0), 2)
        shifts = [random.randint(1, 10)]
        
        backtest_data = {uuid.uuid4().hex: random.random()}
        stress_data = {uuid.uuid4().hex: random.random()}
        drawdown = -0.25

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=backtest_data), \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=stress_data), \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown):
            
            result = self.optimizer.optimize_and_evaluate(rand_symbol, allocation, shifts)
            
            self.assertEqual(result['optimized_weights'], {rand_symbol: allocation})
            self.assertEqual(result['resilience_score'], 1.0 - abs(drawdown))
            self.assertEqual(result['backtest'], backtest_data)
            self.assertEqual(result['stress'], stress_data)

    def test_get_strategy_summary(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        summary = self.optimizer.get_strategy_summary(rand_symbol)
        
        self.assertIn(rand_symbol, summary)
        self.assertEqual(summary[rand_symbol]["summary"], "active")
        self.assertEqual(summary[rand_symbol]["storage"], self.random_storage)