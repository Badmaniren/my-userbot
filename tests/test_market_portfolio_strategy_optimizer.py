import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):
    def setUp(self):
        self.storage_file = uuid.uuid4().hex + ".db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_validate_allocation_valid_float(self):
        val = round(random.uniform(0.0, 1.0), 4)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, val)

    def test_validate_allocation_string_conversion(self):
        val_str = str(round(random.uniform(0.0, 1.0), 4))
        result = self.optimizer._validate_allocation(val_str)
        self.assertEqual(result, float(val_str))

    def test_validate_allocation_out_of_bounds_low(self):
        val = -abs(random.uniform(1.0, 100.0))
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 0.0)

    def test_validate_allocation_out_of_bounds_high(self):
        val = random.uniform(1.0001, 100.0)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 1.0)

    def test_validate_allocation_invalid_type(self):
        invalid_val = uuid.uuid4().hex
        result = self.optimizer._validate_allocation(invalid_val)
        self.assertEqual(result, 0.0)

    def test_optimize_strategy_single_shift(self):
        symbol = uuid.uuid4().hex[:6]
        shift = random.randint(1, 10)
        percentage = round(random.uniform(0.0, 1.0), 2)
        backtest_ret = {uuid.uuid4().hex: random.random()}
        sim_ret = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=backtest_ret) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value=sim_ret) as mock_sim:
            
            res = self.optimizer.optimize_strategy(symbol, shift, percentage)
            mock_bt.assert_called_once_with(symbol, [shift])
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res['backtest'], backtest_ret)
            self.assertEqual(res['simulation'], sim_ret)

    def test_optimize_strategy_iterable_shifts_and_keyerror(self):
        symbol = uuid.uuid4().hex[:6]
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        percentage = round(random.uniform(0.0, 1.0), 2)

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', side_effect=KeyError) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError) as mock_sim:
            
            res = self.optimizer.optimize_strategy(symbol, shifts, percentage)
            mock_bt.assert_called_once_with(symbol, shifts)
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res['backtest'], {})
            self.assertEqual(res['simulation'], {})

    def test_evaluate_resilience_success(self):
        symbol = uuid.uuid4().hex[:6]
        shift = random.randint(1, 5)
        stress_ret = {uuid.uuid4().hex: random.random()}
        drawdown_val = round(-random.uniform(0.0, 0.9), 2)

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=stress_ret) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(symbol, shift)
            mock_stress.assert_called_once_with(symbol, [shift])
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(res['stress_data'], stress_ret)
            self.assertEqual(res['drawdown_checked'], drawdown_val)

    def test_evaluate_resilience_exceptions(self):
        symbol = uuid.uuid4().hex[:6]
        shift = [random.randint(1, 5)]

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=Exception) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(symbol, shift)
            mock_stress.assert_called_once_with(symbol, shift)
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(res['stress_data'], {})
            self.assertEqual(res['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        filepath = uuid.uuid4().hex + ".bin"
        random_bytes = uuid.uuid4().bytes

        with patch('builtins.open', return_value=io.BytesIO(random_bytes)) as mock_file:
            data = self.optimizer.load_strategy_stream(filepath)
            mock_file.assert_called_once_with(filepath, 'rb')
            self.assertEqual(data, random_bytes)

    def test_optimize_and_evaluate_success(self):
        symbol = uuid.uuid4().hex[:6]
        allocation = round(random.uniform(0.0, 1.0), 2)
        shift = random.randint(1, 10)
        backtest_ret = {uuid.uuid4().hex: random.random()}
        stress_ret = {uuid.uuid4().hex: random.random()}
        drawdown_val = str(round(-random.uniform(0.0, 1.0), 2))

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=backtest_ret) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=stress_ret) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            res = self.optimizer.optimize_and_evaluate(symbol, allocation, shift)
            mock_bt.assert_called_once_with(symbol, [shift])
            mock_stress.assert_called_once_with(symbol, [shift])
            mock_dd.assert_called_once_with(symbol)
            
            self.assertEqual(res['optimized_weights'], {symbol: allocation})
            self.assertEqual(res['backtest'], backtest_ret)
            self.assertEqual(res['stress'], stress_ret)
            expected_resilience = 1.0 - abs(float(drawdown_val))
            self.assertEqual(res['resilience_score'], expected_resilience)

    def test_optimize_and_evaluate_exceptions(self):
        symbol = uuid.uuid4().hex[:6]
        allocation = random.uniform(1.5, 5.0) # will be clamped to 1.0
        shift = [random.randint(1, 5)]

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', side_effect=KeyError) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=Exception) as mock_dd:
            
            res = self.optimizer.optimize_and_evaluate(symbol, allocation, shift)
            mock_bt.assert_called_once_with(symbol, shift)
            mock_stress.assert_called_once_with(symbol, shift)
            mock_dd.assert_called_once_with(symbol)
            
            self.assertEqual(res['optimized_weights'], {symbol: 1.0})
            self.assertEqual(res['backtest'], {})
            self.assertEqual(res['stress'], {})
            self.assertEqual(res['resilience_score'], 0.5)

    def test_get_strategy_summary(self):
        symbol = uuid.uuid4().hex[:6]
        summary = self.optimizer.get_strategy_summary(symbol)
        expected = {
            symbol: {
                "summary": "active",
                "storage": self.storage_file
            }
        }
        self.assertEqual(summary, expected)