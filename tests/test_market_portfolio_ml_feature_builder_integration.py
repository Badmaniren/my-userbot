import math
import random
import unittest
import uuid
import numpy as np

from skills.market_portfolio_ml_feature_builder import (
    MarketPortfolioMLFeatureBuilder,
    FeatureBuilderConfigError,
    InsufficientDataError,
    build_ml_features
)


class TestMarketPortfolioMLFeatureBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.asset_id = f"ASSET_{uuid.uuid4().hex[:8]}"
        self.seed_marker = random.randint(100000, 999999)
        self.window_size = random.randint(3, 7)

    def test_pipeline_integration_end_to_end_calculations(self):
        num_points = random.randint(30, 50)
        base_price = round(random.uniform(50.0, 300.0), 2)
        raw_prices = [base_price]
        
        for _ in range(num_points - 1):
            next_price = raw_prices[-1] * (1.0 + random.uniform(-0.05, 0.05))
            raw_prices.append(max(0.1, round(next_price, 4)))

        result = build_ml_features(
            asset_id=self.asset_id,
            data_points=raw_prices,
            window_size=self.window_size,
            seed_marker=self.seed_marker
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["asset_id"], self.asset_id)
        self.assertEqual(result["metadata"]["seed_marker"], self.seed_marker)

        returns = result["log_returns"]
        self.assertEqual(len(returns), len(raw_prices) - 1)
        expected_first_return = math.log(raw_prices[1] / raw_prices[0])
        self.assertAlmostEqual(returns[0], expected_first_return, places=5)

        rolling_vol = result["rolling_volatility"]
        expected_vol_len = (len(returns) - self.window_size + 1) if len(returns) >= self.window_size else 1
        self.assertEqual(len(rolling_vol), expected_vol_len)

        first_chunk = returns[:self.window_size]
        expected_first_vol = float(np.std(first_chunk, ddof=1))
        self.assertAlmostEqual(rolling_vol[0], expected_first_vol, places=5)

        tail_risk = result["tail_risk_metrics"]
        self.assertIn("var", tail_risk)
        self.assertIn("cvar", tail_risk)
        self.assertLessEqual(tail_risk["cvar"], tail_risk["var"])

        builder = MarketPortfolioMLFeatureBuilder(asset_id=self.asset_id, window_size=self.window_size)
        moments = builder.compute_skewness_and_kurtosis(returns)
        self.assertAlmostEqual(result["skewness"], moments["skewness"], places=5)
        self.assertAlmostEqual(result["kurtosis"], moments["kurtosis"], places=5)

    def test_insufficient_data_error_raised(self):
        builder = MarketPortfolioMLFeatureBuilder(asset_id=self.asset_id, window_size=self.window_size)
        single_price = [round(random.uniform(10.0, 100.0), 2)]
        with self.assertRaises(InsufficientDataError):
            builder.compute_log_returns(single_price)

    def test_invalid_window_size_raises_config_error(self):
        invalid_window = random.choice([0, -1, -5])
        with self.assertRaises(FeatureBuilderConfigError):
            MarketPortfolioMLFeatureBuilder(asset_id=self.asset_id, window_size=invalid_window)


if __name__ == "__main__":
    unittest.main()