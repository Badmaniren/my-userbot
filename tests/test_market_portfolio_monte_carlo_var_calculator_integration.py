import unittest
import uuid
import random
from skills.market_portfolio_monte_carlo_var_calculator import calculate_portfolio_var, calculate_monte_carlo_var_and_es

class TestMarketPortfolioMonteCarloVarCalculatorIntegration(unittest.TestCase):
    def test_calculate_portfolio_var_integration_flow(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = round(random.uniform(0.90, 0.99), 2)
        simulations_count = random.randint(500, 2000)

        portfolio_data = {
            "portfolio_id": random_portfolio_id,
            "assets": [
                {"ticker": "AAPL", "weight": 0.5, "value": random.randint(10000, 50000)},
                {"ticker": "GOOGL", "weight": 0.5, "value": random.randint(10000, 50000)}
            ]
        }

        result = calculate_portfolio_var(
            portfolio_data=portfolio_data,
            confidence_level=confidence,
            simulations=simulations_count
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertIn("var", result)
        self.assertIn("expected_shortfall", result)
        self.assertIsInstance(result["var"], float)
        self.assertIsInstance(result["expected_shortfall"], float)
        self.assertGreaterEqual(result["expected_shortfall"], result["var"])

    def test_calculate_monte_carlo_var_and_es_direct_losses(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = round(random.uniform(0.90, 0.99), 2)

        generated_losses = [random.uniform(-500.0, 5000.0) for _ in range(100)]

        result = calculate_monte_carlo_var_and_es(
            portfolio_id=random_portfolio_id,
            confidence=confidence,
            simulations_data=generated_losses
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertIn("var", result)
        self.assertIn("expected_shortfall", result)
        self.assertIsInstance(result["var"], float)
        self.assertIsInstance(result["expected_shortfall"], float)

if __name__ == "__main__":
    unittest.main()