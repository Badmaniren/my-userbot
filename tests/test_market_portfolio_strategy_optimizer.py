import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester'), \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator'):
            self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_validate_allocation_valid_float(self):
        val = random.uniform(0.01, 0.99)
        result = self.optimizer._validate_allocation(val)
        self.assertAlmostEqual(result, val)

    def test_validate_allocation_below_zero(self):
        val = -abs(random.uniform(1.0, 100.0))
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 0.0)

    def test_validate_allocation_above_one(self):
        val = random.uniform(1.01, 100.0)
        result = self.optimizer._validate_allocation(val)
        self.assertEqual(result, 1.0)

    def test_validate_allocation_string_cast(self):
        val = round(random.uniform(0.1, 0.9), 2)
        result = self.optimizer._validate_allocation(str(val))
        self.assertAlmostEqual(result, val)

    def test_validate_allocation_invalid_string(self):
        invalid_str = uuid.uuid4().hex
        result = self.optimizer._validate_allocation(invalid_str)
        self.assertEqual(result, 0.0)

    def test_optimize_strategy_scalar_shift(self):
        symbol = uuid.uuid4().hex[:6]
        shift = random.uniform(0.01, 5.0)
        percentage = random.uniform(1.0, 50.0)
        
        expected_backtest = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_sim = {uuid.uuid4().hex: random.random()}

        self.optimizer.backtester.run_backtest = MagicMock(return_value=expected_backtest)
        self.optimizer.simulator.simulate_scenario = MagicMock(return_value=expected_sim)

        res = self.optimizer.optimize_strategy(symbol, shift, percentage)

        self.optimizer.backtester.run_backtest.assert_called_once_with(symbol, [shift])
        self.optimizer.simulator.simulate_scenario.assert_called_once_with(symbol, percentage)
        self.assertEqual(res['backtest'], expected_backtest)
        self.assertEqual(res['simulation'], expected_sim)

    def test_optimize_strategy_key_error_handling(self):
        symbol = uuid.uuid4().hex[:6]
        shift = [random.uniform(0.1, 1.0)]
        percentage = random.uniform(5.0, 25.0)

        self.optimizer.backtester.run_backtest = MagicMock(side_effect=KeyError)
        self.optimizer.simulator.simulate_scenario = MagicMock(side_effect=KeyError)

        res = self.optimizer.optimize_strategy(symbol, shift, percentage)

        self.assertEqual(res['backtest'], {})
        self.assertEqual(res['simulation'], {})

    def test_evaluate_resilience_success(self):
        symbol = uuid.uuid4().hex[:6]
        shifts = [random.uniform(1.0, 10.0), random.uniform(11.0, 20.0)]
        expected_stress = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_drawdown = -abs(random.uniform(0.1, 0.9))

        self.optimizer.simulator.run_stress_test = MagicMock(return_value=expected_stress)
        self.optimizer.backtester.calculate_maximum_drawdown = MagicMock(return_value=random_drawdown)

        res = self.optimizer.evaluate_resilience(symbol, shifts)

        self.assertEqual(res['stress_data'], expected_stress)
        self.assertEqual(res['drawdown_checked'], random_drawdown)

    def test_evaluate_resilience_string_drawdown_exception(self):
        symbol = uuid.uuid4().hex[:6]
        shift = random.uniform(1.0, 5.0)
        random_dd_str = str(round(random.uniform(-0.9, -0.1), 2))

        self.optimizer.simulator.run_stress_test = MagicMock(side_effect=KeyError)
        self.optimizer.backtester.calculate_maximum_drawdown = MagicMock(return_value=random_dd_str)

        res = self.optimizer.evaluate_resilience(symbol, shift)

        self.assertEqual(res['stress_data'], {})
        self.assertEqual(res['drawdown_checked'], float(random_dd_str))

    def test_load_strategy_stream(self):
        filepath = f"{uuid.uuid4().hex}.bin"
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes

        mock_file = io.BytesIO(random_bytes)
        with patch('builtins.open', return_value=mock_file):
            data = self.optimizer.load_strategy_stream(filepath)

        self.assertEqual(data, random_bytes)

    def test_optimize_and_evaluate_success(self):
        symbol = uuid.uuid4().hex[:6]
        allocation = random.uniform(0.0, 1.0)
        shifts = random.uniform(0.1, 2.0)
        
        expected_backtest = {uuid.uuid4().hex: random.randint(10, 100)}
        expected_stress = {uuid.uuid4().hex: random.randint(1, 10)}
        drawdown_val = -abs(random.uniform(0.0, 0.5))

        self.optimizer.backtester.run_backtest = MagicMock(return_value=expected_backtest)
        self.optimizer.simulator.run_stress_test = MagicMock(return_value=expected_stress)
        self.optimizer.backtester.calculate_maximum_drawdown = MagicMock(return_value=drawdown_val)

        res = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts)

        validated_alloc = self.optimizer._validate_allocation(allocation)
        expected_resilience = 1.0 - abs(drawdown_val)

        self.assertEqual(res["optimized_weights"], {symbol: validated_alloc})
        self.assertAlmostEqual(res["resilience_score"], expected_resilience)
        self.assertEqual(res["backtest"], expected_backtest)
        self.assertEqual(res["stress"], expected_stress)

    def test_optimize_and_evaluate_exceptions_fallback(self):
        symbol = uuid.uuid4().hex[:6]
        allocation = random.uniform(1.5, 5.0)
        shifts = [random.uniform(1.0, 3.0)]

        self.optimizer.backtester.run_backtest = MagicMock(side_effect=KeyError)
        self.optimizer.simulator.run_stress_test = MagicMock(side_effect=KeyError)
        self.optimizer.backtester.calculate_maximum_drawdown = MagicMock(side_effect=Exception)

        res = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts)

        self.assertEqual(res["optimized_weights"], {symbol: 1.0})
        self.assertEqual(res["resilience_score"], 0.5)
        self.assertEqual(res["backtest"], {})
        self.assertEqual(res["stress"], {})

    def test_get_strategy_summary(self):
        symbol = uuid.uuid4().hex[:6]
        summary = self.optimizer.get_strategy_summary(symbol)

        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_file)