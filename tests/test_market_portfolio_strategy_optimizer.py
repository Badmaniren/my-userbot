import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer


class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_optimize_strategy(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        percentage = round(random.uniform(0.01, 0.99), 4)

        mock_backtest_result = {uuid.uuid4().hex: random.random()}
        mock_simulation_result = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=mock_backtest_result) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value=mock_simulation_result) as mock_sim:

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            mock_bt.assert_called_once_with(symbol, shifts)
            mock_sim.assert_called_once_with(symbol, percentage)

            self.assertIn('backtest', result)
            self.assertIn('simulation', result)
            self.assertEqual(result['backtest'], mock_backtest_result)
            self.assertEqual(result['simulation'], mock_simulation_result)

    def test_evaluate_resilience(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = random.randint(1, 50)

        mock_stress_data = {uuid.uuid4().hex: random.randint(100, 500)}
        mock_drawdown_checked = round(random.uniform(-0.5, 0.0), 4)

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=mock_stress_data) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=mock_drawdown_checked) as mock_dd:

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            mock_stress.assert_called_once_with(symbol, shifts)
            mock_dd.assert_called_once_with(symbol)

            self.assertIn('stress_data', result)
            self.assertIn('drawdown_checked', result)
            self.assertEqual(result['stress_data'], mock_stress_data)
            self.assertEqual(result['drawdown_checked'], mock_drawdown_checked)

    def test_load_strategy_stream(self):
        filepath = f"{uuid.uuid4().hex}.bin"
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes

        mock_file = io.BytesIO(random_bytes)

        with patch('builtins.open', return_value=mock_file) as mock_op:
            stream_data = self.optimizer.load_strategy_stream(filepath)

            mock_op.assert_called_once_with(filepath, 'rb')
            self.assertEqual(stream_data, random_bytes)

    def test_optimize_and_evaluate_with_scalar_shift(self):
        symbol = uuid.uuid4().hex[:6].upper()
        allocation = round(random.uniform(0.1, 1.0), 2)
        scalar_shift = random.randint(1, 100)

        mock_backtest_res = {uuid.uuid4().hex: random.random()}
        mock_stress_res = {uuid.uuid4().hex: random.random()}
        mock_drawdown = round(random.uniform(-0.8, -0.1), 2)

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=mock_backtest_res) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=mock_stress_res) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=str(mock_drawdown)) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, scalar_shift)

            mock_bt.assert_called_once_with(symbol, [scalar_shift])
            mock_stress.assert_called_once_with(symbol, [scalar_shift])
            mock_dd.assert_called_once_with(symbol)

            self.assertEqual(result["optimized_weights"], {symbol: allocation})
            self.assertEqual(result["resilience_score"], 1.0 - abs(mock_drawdown))
            self.assertEqual(result["backtest"], mock_backtest_res)
            self.assertEqual(result["stress"], mock_stress_res)

    def test_optimize_and_evaluate_with_iterable_shifts_and_exception(self):
        symbol = uuid.uuid4().hex[:6].upper()
        allocation = round(random.uniform(0.1, 1.0), 2)
        shifts_list = [random.randint(1, 10), random.randint(11, 20)]

        mock_backtest_res = {uuid.uuid4().hex: random.random()}
        mock_stress_res = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=mock_backtest_res) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=mock_stress_res) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=ValueError("Corrupted drawdown")) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts_list)

            mock_bt.assert_called_once_with(symbol, shifts_list)
            mock_stress.assert_called_once_with(symbol, shifts_list)
            mock_dd.assert_called_once_with(symbol)

            self.assertEqual(result["optimized_weights"], {symbol: allocation})
            self.assertEqual(result["resilience_score"], 0.5)
            self.assertEqual(result["backtest"], mock_backtest_res)
            self.assertEqual(result["stress"], mock_stress_res)

    def test_get_strategy_summary(self):
        symbol = uuid.uuid4().hex[:6].upper()
        summary = self.optimizer.get_strategy_summary(symbol)

        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_file)


if __name__ == '__main__':
    unittest.main()