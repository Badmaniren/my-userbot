import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file_path = uuid.uuid4().hex + ".db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file_path)

    def test_optimize_strategy_success(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = [random.randint(1, 30), random.randint(31, 60)]
        percentage = random.uniform(0.01, 1.0)

        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_simulation = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=expected_backtest) as mock_backtest, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_simulation) as mock_simulate:

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            mock_backtest.assert_called_once_with(symbol, shifts)
            mock_simulate.assert_called_once_with(symbol, percentage)
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['simulation'], expected_simulation)

    def test_optimize_strategy_key_error_fallback(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = random.randint(1, 10)
        percentage = random.uniform(0.1, 0.9)

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', side_effect=KeyError), \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError):

            result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

            self.assertEqual(result, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_success(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = (random.randint(1, 5), random.randint(6, 10))
        stress_key = uuid.uuid4().hex
        stress_val = random.random()
        drawdown_str = str(random.uniform(-0.5, -0.01))

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value={stress_key: stress_val}) as mock_stress, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_str) as mock_dd:

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            mock_stress.assert_called_once_with(symbol, shifts)
            mock_dd.assert_called_once_with(symbol)
            self.assertEqual(result['stress_data'], {stress_key: stress_val})
            self.assertEqual(result['drawdown_checked'], float(drawdown_str))

    def test_evaluate_resilience_exceptions_fallback(self):
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = random.randint(1, 100)

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError), \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=Exception):

            result = self.optimizer.evaluate_resilience(symbol, shifts)

            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        filepath = uuid.uuid4().hex + ".bin"
        random_bytes = uuid.uuid4().bytes + os.urandom(16)

        mock_file = io.BytesIO(random_bytes)

        with patch('builtins.open', return_value=mock_file) as mock_open:
            data = self.optimizer.load_strategy_stream(filepath)

            mock_open.assert_called_once_with(filepath, 'rb')
            self.assertEqual(data, random_bytes)

    def test_optimize_and_evaluate_with_scalar_shift(self):
        symbol = uuid.uuid4().hex[:6].upper()
        allocation = random.uniform(10.0, 1000.0)
        scalar_shift = random.randint(1, 50)
        
        backtest_data = {uuid.uuid4().hex: random.randint(1, 100)}
        stress_data = {uuid.uuid4().hex: random.randint(100, 200)}
        drawdown_val = -random.uniform(0.1, 0.4)

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', return_value=backtest_data) as mock_bt, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=stress_data) as mock_st, \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, scalar_shift)

            mock_bt.assert_called_once_with(symbol, [scalar_shift])
            mock_st.assert_called_once_with(symbol, [scalar_shift])
            mock_dd.assert_called_once_with(symbol)

            self.assertEqual(result["optimized_weights"], {symbol: allocation})
            self.assertAlmostEqual(result["resilience_score"], 1.0 - abs(drawdown_val))
            self.assertEqual(result["backtest"], backtest_data)
            self.assertEqual(result["stress"], stress_data)

    def test_optimize_and_evaluate_fallback_on_errors(self):
        symbol = uuid.uuid4().hex[:6].upper()
        allocation = random.uniform(1.0, 50.0)
        shifts = [random.randint(1, 10)]

        with patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.run_backtest', side_effect=KeyError), \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError), \
             patch('skills.market_portfolio_backtester.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=TypeError):

            result = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts)

            self.assertEqual(result["optimized_weights"], {symbol: allocation})
            self.assertEqual(result["resilience_score"], 0.5)
            self.assertEqual(result["backtest"], {})
            self.assertEqual(result["stress"], {})

    def test_get_strategy_summary(self):
        symbol = uuid.uuid4().hex[:8].lower()
        summary = self.optimizer.get_strategy_summary(symbol)

        expected_dict = {
            symbol: {
                "summary": "active",
                "storage": self.storage_file_path
            }
        }
        self.assertEqual(summary, expected_dict)

if __name__ == '__main__':
    unittest.main()