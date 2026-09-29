import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer


class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_validate_allocation_boundary_and_types(self):
        rand_valid = round(random.uniform(0.0, 1.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(rand_valid), rand_valid)

        over_val = 1.0 + random.uniform(0.1, 10.0)
        self.assertEqual(self.optimizer._validate_allocation(over_val), 1.0)

        under_val = -1.0 * random.uniform(0.1, 10.0)
        self.assertEqual(self.optimizer._validate_allocation(under_val), 0.0)

        str_num = str(round(random.uniform(0.0, 1.0), 2))
        self.assertEqual(self.optimizer._validate_allocation(str_num), float(str_num))

        rand_chars = ''.join(random.choices(string.ascii_letters, k=8))
        self.assertEqual(self.optimizer._validate_allocation(rand_chars), 0.0)

        self.assertEqual(self.optimizer._validate_allocation(None), 0.0)

    def test_optimize_strategy_success_and_key_error(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shift_val = random.randint(1, 100)
        percentage = round(random.uniform(1.0, 50.0), 2)
        expected_backtest = {uuid.uuid4().hex: random.randint(100, 999)}
        expected_sim = {uuid.uuid4().hex: random.uniform(0.0, 1.0)}

        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', return_value=expected_backtest) as mock_bt, \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_sim) as mock_sim:
            
            result = self.optimizer.optimize_strategy(symbol, shift_val, percentage)
            self.assertEqual(result['backtest'], expected_backtest)
            self.assertEqual(result['simulation'], expected_sim)
            mock_bt.assert_called_once_with(symbol, [shift_val])
            mock_sim.assert_called_once_with(symbol, percentage)

        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', side_effect=KeyError) as mock_bt, \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError) as mock_sim:
            
            result = self.optimizer.optimize_strategy(symbol, [shift_val], percentage)
            self.assertEqual(result['backtest'], {})
            self.assertEqual(result['simulation'], {})

    def test_evaluate_resilience_success_and_exceptions(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        expected_stress = {uuid.uuid4().hex: random.random()}
        raw_drawdown = round(random.uniform(-0.9, -0.1), 2)

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', return_value=expected_stress) as mock_stress, \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=raw_drawdown) as mock_dd:
            
            result = self.optimizer.evaluate_resilience(symbol, shifts)
            self.assertEqual(result['stress_data'], expected_stress)
            self.assertEqual(result['drawdown_checked'], raw_drawdown)
            mock_stress.assert_called_once_with(symbol, shifts)
            mock_dd.assert_called_once_with(symbol)

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', side_effect=KeyError), \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', side_effect=Exception):
            
            result = self.optimizer.evaluate_resilience(symbol, shifts[0])
            self.assertEqual(result['stress_data'], {})
            self.assertEqual(result['drawdown_checked'], 0.0)

    def test_load_strategy_stream_io(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        filepath = f"path_{uuid.uuid4().hex}.bin"

        mock_file = io.BytesIO(random_bytes)
        with patch('builtins.open', return_value=mock_file) as mock_op:
            stream_data = self.optimizer.load_strategy_stream(filepath)
            self.assertEqual(stream_data, random_bytes)
            mock_op.assert_called_once_with(filepath, 'rb')

    def test_optimize_and_evaluate_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        allocation = round(random.uniform(0.0, 1.0), 2)
        shift = random.randint(1, 50)
        backtest_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        stress_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        drawdown_val = -0.25

        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.run_backtest', return_value=backtest_payload), \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator.run_stress_test', return_value=stress_payload), \
             patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester.calculate_maximum_drawdown', return_value=drawdown_val):
            
            res = self.optimizer.optimize_and_evaluate(symbol, allocation, shift)
            
            self.assertEqual(res['optimized_weights'], {symbol: allocation})
            self.assertEqual(res['resilience_score'], 1.0 - abs(drawdown_val))
            self.assertEqual(res['backtest'], backtest_payload)
            self.assertEqual(res['stress'], stress_payload)

    def test_get_strategy_summary(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        summary = self.optimizer.get_strategy_summary(symbol)
        
        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_file)