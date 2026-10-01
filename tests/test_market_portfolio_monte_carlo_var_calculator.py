import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
import sys

class MockNumpy:
    def array(self, val, *args, **kwargs):
        return val
    def percentile(self, a, q, *args, **kwargs):
        if not a:
            return 0.0
        return float(sorted(a)[int(len(a) * q / 100)])
    def mean(self, a, *args, **kwargs):
        if not a:
            return 0.0
        return float(sum(a) / len(a))
    def __getattr__(self, name):
        return MagicMock()

sys.modules['numpy'] = MockNumpy()

from skills.market_portfolio_monte_carlo_var_calculator import (
    MarketPortfolioMonteCarloVarCalculator,
    VaRCalculationError,
    market_portfolio_monte_carlo_var_calculator
)

class TestMarketPortfolioMonteCarloVarCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.80, 0.99), 2)
        self.simulation_runs = random.randint(100, 1000)
        self.initial_value = round(random.uniform(10000.0, 500000.0), 2)

    def test_init_valid_confidence(self):
        calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
        self.assertEqual(calc.portfolio_id, self.portfolio_id)
        self.assertEqual(calc.confidence_level, self.confidence_level)
        self.assertEqual(calc.simulation_runs, self.simulation_runs)

    def test_init_invalid_confidence_zero(self):
        with self.assertRaises(ValueError):
            MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, 0.0, self.simulation_runs)

    def test_init_invalid_confidence_one(self):
        with self.assertRaises(ValueError):
            MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, 1.0, self.simulation_runs)

    def test_init_invalid_confidence_negative(self):
        with self.assertRaises(ValueError):
            MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, -random.uniform(0.1, 5.0), self.simulation_runs)

    def test_init_invalid_confidence_greater_than_one(self):
        with self.assertRaises(ValueError):
            MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, 1.0 + random.uniform(0.1, 5.0), self.simulation_runs)

    def test_calculate_var_success(self):
        simulated_values = [self.initial_value * random.uniform(0.8, 1.2) for _ in range(self.simulation_runs)]

        with patch('skills.market_portfolio_stress_monte_carlo_engine.run_simulations') as mock_run:
            mock_run.return_value = simulated_values
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            result = calc.calculate_var(self.initial_value)

            self.assertIsInstance(result, dict)
            self.assertEqual(result['portfolio_id'], self.portfolio_id)
            self.assertEqual(result['confidence_level'], self.confidence_level)
            self.assertIn('var_absolute', result)
            self.assertIn('var_percentage', result)
            self.assertIn('expected_shortfall', result)

    def test_calculate_var_empty_simulations(self):
        with patch('skills.market_portfolio_stress_monte_carlo_engine.run_simulations') as mock_run:
            mock_run.return_value = []
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            with self.assertRaises(VaRCalculationError):
                calc.calculate_var(self.initial_value)

    def test_calculate_expected_shortfall_success(self):
        simulated_values = [self.initial_value * random.uniform(0.7, 1.3) for _ in range(self.simulation_runs)]

        with patch('skills.market_portfolio_stress_monte_carlo_engine.run_simulations') as mock_run:
            mock_run.return_value = simulated_values
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            result = calc.calculate_expected_shortfall(self.initial_value, simulated_values=simulated_values)

            self.assertIsInstance(result, dict)
            self.assertIn('expected_shortfall_absolute', result)
            self.assertIn('expected_shortfall_percentage', result)

    def test_calculate_expected_shortfall_empty(self):
        calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
        with self.assertRaises(VaRCalculationError):
            calc.calculate_expected_shortfall(self.initial_value, simulated_values=[])

    def test_calculate_var_with_audit(self):
        simulated_values = [self.initial_value * random.uniform(0.9, 1.1) for _ in range(self.simulation_runs)]
        endpoint = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_monte_carlo_engine.run_simulations') as mock_run, \
             patch('skills.market_portfolio_audit_log_exporter.export_metric') as mock_export:
            mock_run.return_value = simulated_values
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            result = calc.calculate_var_with_audit(self.initial_value, endpoint)

            self.assertEqual(result['portfolio_id'], self.portfolio_id)
            mock_export.assert_called_once()

    def test_load_historical_volatility_stream(self):
        stream_content = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        with patch('skills.db_storage.fetch_stream') as mock_fetch:
            mock_fetch.return_value = mock_stream
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            loaded_data = calc.load_historical_volatility_stream(self.portfolio_id)

            self.assertEqual(loaded_data, stream_content.decode('utf-8'))
            mock_fetch.assert_called_once_with(self.portfolio_id)

    def test_calculate_var_and_dispatch_triggered(self):
        simulated_values = [self.initial_value * 0.5 for _ in range(self.simulation_runs)]
        threshold = 0.01
        topic = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_monte_carlo_engine.run_simulations') as mock_run, \
             patch('skills.market_portfolio_alert_dispatcher.dispatch_alert') as mock_dispatch:
            mock_run.return_value = simulated_values
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            result = calc.calculate_var_and_dispatch(self.initial_value, threshold, topic)

            self.assertGreater(result['var_percentage'], threshold)
            mock_dispatch.assert_called_once()

    def test_calculate_var_and_dispatch_not_triggered(self):
        simulated_values = [self.initial_value for _ in range(self.simulation_runs)]
        threshold = 0.99
        topic = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_monte_carlo_engine.run_simulations') as mock_run, \
             patch('skills.market_portfolio_alert_dispatcher.dispatch_alert') as mock_dispatch:
            mock_run.return_value = simulated_values
            calc = MarketPortfolioMonteCarloVarCalculator(self.portfolio_id, self.confidence_level, self.simulation_runs)
            result = calc.calculate_var_and_dispatch(self.initial_value, threshold, topic)

            mock_dispatch.assert_not_called()

    def test_functional_wrapper_no_paths(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence_level,
            "simulation_data": {
                "initial_value": self.initial_value
            }
        }

        with patch('skills.db_storage') as mock_db:
            res = market_portfolio_monte_carlo_var_calculator(payload)
            self.assertEqual(res['portfolio_id'], self.portfolio_id)
            self.assertEqual(res['confidence_level'], self.confidence_level)
            self.assertIn('var_value', res)
            self.assertIn('expected_shortfall', res)
            mock_db.assert_called_once()

    def test_functional_wrapper_with_paths(self):
        paths = [[self.initial_value, self.initial_value * random.uniform(0.8, 1.1)] for _ in range(10)]
        payload = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence_level,
            "simulation_data": {
                "initial_value": self.initial_value,
                "simulation_paths": paths
            }
        }

        with patch('skills.db_storage') as mock_db:
            res = market_portfolio_monte_carlo_var_calculator(payload)
            self.assertEqual(res['portfolio_id'], self.portfolio_id)
            self.assertIn('var_value', res)
            mock_db.assert_called_once()