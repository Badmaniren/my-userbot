import unittest
from unittest.mock import patch
import random
import uuid
import io
import sys

try:
    import numpy
except ImportError:
    class DummyNumpy:
        class ndarray:
            pass
        def array(self, lst, dtype=None):
            return lst
        def sort(self, arr):
            return sorted(arr)
        def ceil(self, val):
            import math
            return math.ceil(val)
        def mean(self, lst):
            if not lst:
                return 0.0
            return sum(lst) / len(lst)

    sys.modules['numpy'] = DummyNumpy()

from skills.market_portfolio_monte_carlo_var_calculator import (
    _compute_var_and_es,
    calculate_portfolio_var,
    calculate_monte_carlo_var_and_es
)

class TestMarketPortfolioMonteCarloVarCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.simulations = random.randint(100, 2000)
        self.raw_losses = [random.uniform(-100.0, 1000.0) for _ in range(50)]

    def test_compute_var_and_es_empty(self):
        var_val, es_val = _compute_var_and_es([], confidence_level=self.confidence_level)
        self.assertEqual(var_val, 0.0)
        self.assertEqual(es_val, 0.0)

    def test_compute_var_and_es_non_empty(self):
        var_val, es_val = _compute_var_and_es(self.raw_losses, confidence_level=self.confidence_level)
        self.assertIsInstance(var_val, float)
        self.assertIsInstance(es_val, float)

    def test_calculate_monte_carlo_var_and_es_list_input(self):
        result = calculate_monte_carlo_var_and_es(
            portfolio_id=self.portfolio_id,
            confidence=self.confidence_level,
            simulations_data=self.raw_losses
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var", result)
        self.assertIn("expected_shortfall", result)

    def test_calculate_monte_carlo_var_and_es_dict_input(self):
        sim_data = {"portfolio_loss_distribution": self.raw_losses}
        result = calculate_monte_carlo_var_and_es(
            portfolio_id=self.portfolio_id,
            confidence=self.confidence_level,
            simulations_data=sim_data
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)

    def test_calculate_portfolio_var_with_datstream(self):
        portfolio_data = {"portfolio_id": self.portfolio_id, "random_key": uuid.uuid4().hex}
        dummy_stream = io.BytesIO(uuid.uuid4().bytes)

        engine_mock_return = {"portfolio_loss_distribution": self.raw_losses}

        with patch("skills.market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress", return_value=engine_mock_return) as mock_engine:
            result = calculate_portfolio_var(
                portfolio_data=portfolio_data,
                confidence_level=self.confidence_level,
                simulations=self.simulations,
                data_stream=dummy_stream
            )
            mock_engine.assert_called_once_with(
                portfolio_data=portfolio_data,
                simulations=self.simulations
            )
            self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
            self.assertIn("var", result)
            self.assertIn("expected_shortfall", result)

if __name__ == "__main__":
    unittest.main()