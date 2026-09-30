import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
from skills.market_portfolio_stress_monte_carlo_resiliency_engine import (
    start_new,
    market_portfolio_stress_monte_carlo_resiliency_engine
)


class TestMarketPortfolioStressMonteCarloResiliencyEngine(unittest.TestCase):

    def test_start_new_basic_completion(self):
        result = start_new()
        self.assertIn("status", result)
        self.assertEqual(result["status"], "completed")

    def test_start_new_with_parameters(self):
        rand_iterations = random.randint(100, 5000)
        rand_shock = round(random.uniform(0.05, 0.95), 2)

        result = start_new(iterations=rand_iterations, shock_factor=rand_shock)
        self.assertIn("iterations_processed", result)
        self.assertIn("applied_shock", result)
        self.assertEqual(result["iterations_processed"], rand_iterations)
        self.assertEqual(result["applied_shock"], rand_shock)

    def test_market_portfolio_stress_monte_carlo_resiliency_engine_calculation(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_total_value = round(random.uniform(10000.0, 1000000.0), 2)
        rand_shock_factor = round(random.uniform(0.1, 0.5), 2)

        payload = {
            "portfolio_id": rand_portfolio_id,
            "baseline_valuation": {
                "total_value": rand_total_value
            },
            "shock_factor": rand_shock_factor
        }

        result = market_portfolio_stress_monte_carlo_resiliency_engine(payload)

        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["status"], "success")

        expected_score = max(0.0, min(100.0, 100.0 * (1.0 - rand_shock_factor)))
        self.assertAlmostEqual(result["resiliency_score"], expected_score)

        expected_var = rand_total_value * rand_shock_factor * 0.8
        self.assertAlmostEqual(result["var_95"], expected_var)

        expected_shortfall = rand_total_value * rand_shock_factor * 1.2
        self.assertAlmostEqual(result["expected_shortfall"], expected_shortfall)

    def test_market_portfolio_stress_engine_default_payload(self):
        payload = {}
        result = market_portfolio_stress_monte_carlo_resiliency_engine(payload)

        self.assertEqual(result["status"], "success")
        self.assertIn("resiliency_score", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)

    def test_start_new_io_stream_handling(self):
        garbage_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        stream = io.BytesIO(garbage_bytes)

        with patch("sys.stdin", stream):
            read_data = stream.read()
            self.assertEqual(read_data, garbage_bytes)


if __name__ == "__main__":
    unittest.main()