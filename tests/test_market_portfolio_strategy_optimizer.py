import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file_path = f"{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file_path)
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_percentage = round(random.uniform(0.1, 100.0), 2)
        self.random_shifts = [random.randint(1, 30), random.randint(31, 60)]
        self.random_allocation = round(random.uniform(0.01, 1.0), 4)

    def test_optimize_strategy_success(self):
        expected_backtest = {uuid.uuid4().hex: random.randint(100, 500)}
        expected_simulation = {uuid.uuid4().hex: random.uniform(10.0, 50.0)}

        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', return_value=expected_backtest) as mock_backtest, \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_simulation) as mock_sim:

            result = self.optimizer.optimize_strategy(self.random_symbol, self.random_shifts, self.random_percentage)

            mock_backtest.assert_called_once_with(self.random_symbol, self.random_shifts)
            mock_sim.assert_called_once_with(self.random_symbol, self.random_percentage)
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['simulation'], expected_simulation)

    def test_optimize_strategy_key_error_handling(self):
        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', side_effect=KeyError) as mock_backtest, \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError) as mock_sim:

            result = self.optimizer.optimize_strategy(self.random_symbol, self.random_shifts, self.random_percentage)

            self.assertEqual(result, {'backtest': {}, 'simulation': {}})

    def test_evaluate_resilience_success(self):
        expected_stress = {uuid.uuid4().hex: random.random()}
        expected_drawdown = round(random.uniform(-0.5, -0.01), 4)

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', return_value=expected_stress) as mock_stress, \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=str(expected_drawdown)) as mock_dd:

            result = self.optimizer.evaluate_resilience(self.random_symbol, self.random_shifts)

            mock_stress.assert_called_once_with(self.random_symbol, self.random_shifts)
            mock_dd.assert_called_once_with(self.random_symbol)
            self.assertEqual(result['stress_data'], expected_stress)
            self.assertEqual(result['drawdown_checked'], float(expected_drawdown))

    def test_evaluate_resilience_exception_fallback(self):
        with patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError) as mock_stress, \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=Exception) as mock_dd:

            result = self.optimizer.evaluate_resilience(self.random_symbol, self.random_shifts)

            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        random_bytes = uuid.uuid4().bytes + os.urandom(16) if 'os' in globals() else uuid.uuid4().bytes
        fake_filepath = f"{uuid.uuid4().hex}.bin"

        mock_file = io.BytesIO(random_bytes)
        with patch('builtins.open', return_value=mock_file) as mock_open:
            stream_data = self.optimizer.load_strategy_stream(fake_filepath)
            
            mock_open.assert_called_once_with(fake_filepath, 'rb')
            self.assertEqual(stream_data, random_bytes)

    def test_optimize_and_evaluate_with_scalar_shift(self):
        scalar_shift = random.randint(1, 10)
        expected_backtest = {uuid.uuid4().hex: random.random()}
        expected_stress = {uuid.uuid4().hex: random.random()}
        drawdown_val = -0.25

        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', return_value=expected_backtest) as mock_bt, \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', return_value=expected_stress) as mock_st, \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:

            result = self.optimizer.optimize_and_evaluate(self.random_symbol, self.random_allocation, scalar_shift)

            mock_bt.assert_called_once_with(self.random_symbol, [scalar_shift])
            mock_st.assert_called_once_with(self.random_symbol, [scalar_shift])
            mock_dd.assert_called_once_with(self.random_symbol)

            self.assertEqual(result['optimized_weights'], {self.random_symbol: self.random_allocation})
            self.assertEqual(result['resilience_score'], 1.0 - abs(drawdown_val))
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['stress'], expected_stress)

    def test_optimize_and_evaluate_exceptions_handling(self):
        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', side_effect=KeyError), \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError), \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=Exception):

            result = self.optimizer.optimize_and_evaluate(self.random_symbol, self.random_allocation, self.random_shifts)

            self.assertEqual(result['optimized_weights'], {self.random_symbol: self.random_allocation})
            self.assertEqual(result['resilience_score'], 0.5)
            self.assertEqual(result['backtest'], {})
            self.assertEqual(result['stress'], {})

    def test_get_strategy_summary(self):
        summary = self.optimizer.get_strategy_summary(self.random_symbol)
        
        self.assertIn(self.random_symbol, summary)
        self.assertEqual(summary[self.random_symbol]["summary"], "active")
        self.assertEqual(summary[self.random_symbol]["storage"], self.storage_file_path)

if __name__ == '__main__':
    unittest.main()