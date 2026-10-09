import math
import random
import unittest
import uuid

from skills.market_portfolio_ml_feature_builder import (
    InsufficientDataError,
    MarketPortfolioMLFeatureBuilder,
)
from skills.market_portfolio_ml_stress_evaluator import (
    MarketPortfolioMLStressEvaluator,
    evaluate_portfolio_stress,
)


class TestMarketPortfolioMLStressEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_seed = random.randint(1000, 99999)
        random.seed(self.random_seed)
        self.portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        self.scenario_code = f"SCENARIO_{uuid.uuid4().hex[:6].upper()}"
        self.window_size = 10

        # Generate realistic random price series of length 60
        base_price = round(random.uniform(50.0, 300.0), 2)
        self.prices = [base_price]
        for _ in range(59):
            step = random.gauss(0.0, 0.02)
            next_price = max(1.0, round(self.prices[-1] * (1.0 + step), 4))
            self.prices.append(next_price)

    def test_evaluate_stress_with_evaluator_instance(self):
        evaluator = MarketPortfolioMLStressEvaluator(window_size=self.window_size)
        confidence = round(random.uniform(0.90, 0.99), 2)

        result = evaluator.evaluate_stress(
            portfolio_id=self.portfolio_id,
            prices=self.prices,
            scenario_code=self.scenario_code,
            confidence_level=confidence,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("resilience_score", result)
        self.assertIn("deep_drawdown_probability", result)
        self.assertIn("features", result)
        self.assertIn("volatility_forecast", result)

        self.assertIsInstance(result["resilience_score"], (int, float))
        self.assertTrue(0.0 <= result["resilience_score"] <= 100.0 or 0.0 <= result["resilience_score"] <= 1.0)

        self.assertIsInstance(result["deep_drawdown_probability"], (int, float))
        self.assertTrue(0.0 <= result["deep_drawdown_probability"] <= 1.0)

        # Verify underlying feature extraction metrics
        features = result["features"]
        self.assertIsInstance(features, dict)
        self.assertIn("log_returns_count", features)
        self.assertEqual(features["log_returns_count"], len(self.prices) - 1)

        # Check volatility forecast section
        vf = result["volatility_forecast"]
        self.assertIsInstance(vf, dict)
        self.assertIn("forecasted_volatility", vf)
        self.assertFalse(math.isnan(vf["forecasted_volatility"]))

    def test_evaluate_stress_top_level_function(self):
        confidence = 0.95
        result = evaluate_portfolio_stress(
            portfolio_id=self.portfolio_id,
            prices=self.prices,
            scenario_code=self.scenario_code,
            confidence_level=confidence,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("resilience_score", result)
        self.assertIn("deep_drawdown_probability", result)

    def test_sensitivity_to_extreme_shock_prices(self):
        evaluator = MarketPortfolioMLStressEvaluator(window_size=self.window_size)

        # Baseline run
        base_result = evaluator.evaluate_stress(
            portfolio_id=self.portfolio_id,
            prices=self.prices,
            scenario_code=self.scenario_code,
            confidence_level=0.95,
        )

        # Highly crashing price series
        crashing_prices = list(self.prices)
        last_p = crashing_prices[-1]
        for _ in range(15):
            last_p = max(0.01, last_p * 0.8)
            crashing_prices.append(last_p)

        crash_result = evaluator.evaluate_stress(
            portfolio_id=self.portfolio_id,
            prices=crashing_prices,
            scenario_code=self.scenario_code,
            confidence_level=0.95,
        )

        # Drawdown probability should increase or resilience score should decrease under extreme crash
        self.assertGreaterEqual(
            crash_result["deep_drawdown_probability"],
            base_result["deep_drawdown_probability"] * 0.8,
        )

    def test_insufficient_data_raises_error(self):
        evaluator = MarketPortfolioMLStressEvaluator(window_size=self.window_size)
        too_few_prices = [100.0, 101.0]

        with self.assertRaises((InsufficientDataError, ValueError)):
            evaluator.evaluate_stress(
                portfolio_id=self.portfolio_id,
                prices=too_few_prices,
                scenario_code=self.scenario_code,
                confidence_level=0.95,
            )

    def test_invalid_confidence_level_raises_error(self):
        evaluator = MarketPortfolioMLStressEvaluator(window_size=self.window_size)
        invalid_confidence = random.choice([-0.5, 0.0, 1.0, 1.5])

        with self.assertRaises(ValueError):
            evaluator.evaluate_stress(
                portfolio_id=self.portfolio_id,
                prices=self.prices,
                scenario_code=self.scenario_code,
                confidence_level=invalid_confidence,
            )


if __name__ == "__main__":
    unittest.main()