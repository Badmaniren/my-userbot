import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.filepath = f"{uuid.uuid4().hex}.csv"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except OSError:
                pass

    def test_composition_and_initialization(self):
        optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.assertEqual(optimizer.storage_file, self.storage_file)
        self.assertIsNotNone(optimizer.backtester)
        self.assertIsNotNone(optimizer.simulator)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_optimize_strategy_delegation(self, mock_simulator_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_simulator_instance = mock_simulator_cls.return_value

        expected_metric = random.uniform(10.0, 500.0)
        mock_backtester_instance.run_backtest.return_value = {'metric': expected_metric}
        mock_simulator_instance.simulate_scenario.return_value = {'simulation': 'success'}

        optimizer = PortfolioStrategyOptimizer(self.storage_file)
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        percentage = random.uniform(-15.0, 15.0)

        result = optimizer.optimize_strategy(self.symbol, shifts, percentage)

        mock_backtester_instance.run_backtest.assert_called_once()
        mock_simulator_instance.simulate_scenario.assert_called_once_with(self.symbol, percentage)
        self.assertIn('backtest', result)
        self.assertIn('simulation', result)

    @patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester')
    @patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator')
    def test_evaluate_resilience_logic(self, mock_simulator_cls, mock_backtester_cls):
        mock_backtester_instance = mock_backtester_cls.return_value
        mock_simulator_instance = mock_simulator_cls.return_value

        stress_result = {'stress_level': uuid.uuid4().hex}
        mock_simulator_instance.run_stress_test.return_value = stress_result

        drawdown_val = random.uniform(0.01, 0.99)
        mock_backtester_instance.calculate_maximum_drawdown.return_value = drawdown_val

        optimizer = PortfolioStrategyOptimizer(self.storage_file)
        shifts = [random.randint(1, 5), random.randint(6, 10)]

        resilience = optimizer.evaluate_resilience(self.symbol, shifts)

        mock_simulator_instance.run_stress_test.assert_called_once_with(self.symbol, shifts)
        self.assertEqual(resilience['stress_data'], stress_result)
        self.assertIn('drawdown_checked', resilience)

    def test_io_stream_handling(self):
        optimizer = PortfolioStrategyOptimizer(self.storage_file)
        mock_stream = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = mock_stream
            result = optimizer.load_strategy_stream(self.filepath)
            self.assertIsNotNone(result)