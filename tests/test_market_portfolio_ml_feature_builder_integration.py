import unittest
import uuid
import random
import os
from skills.market_portfolio_ml_feature_builder import build_ml_features
from skills.db_storage import save_feature_set, load_feature_set
from skills.market_portfolio_collector_agent import collect_historical_prices

class TestMarketPortfolioMlFeatureBuilderIntegration(unittest.TestCase):

    def test_ml_feature_builder_pipeline_integration(self):
        asset_id = f"ASSET_{uuid.uuid4().hex[:8]}"
        run_identifier = uuid.uuid4().int

        raw_prices = [round(100.0 + random.uniform(-5.0, 5.0) + i * random.uniform(-0.5, 0.5), 4) for i in range(50)]
        
        ingestion_result = collect_historical_prices(asset_id, raw_prices)
        self.assertIsNotNone(ingestion_result)

        feature_output = build_ml_features(
            asset_id=asset_id,
            data_points=raw_prices,
            window_size=10,
            seed_marker=run_identifier
        )

        self.assertIn("log_returns", feature_output)
        self.assertIn("rolling_volatility", feature_output)
        self.assertIn("skewness", feature_output)
        self.assertIn("kurtosis", feature_output)
        self.assertIn("tail_risk_metrics", feature_output)
        
        self.assertEqual(feature_output["metadata"]["seed_marker"], run_identifier)

        storage_token = f"TOKEN_{uuid.uuid4().hex}"
        save_status = save_feature_set(storage_token, feature_output)
        self.assertTrue(save_status)

        loaded_data = load_feature_set(storage_token)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data["metadata"]["seed_marker"], run_identifier)
        self.assertEqual(len(loaded_data["log_returns"]), len(raw_prices) - 1)

if __name__ == "__main__":
    unittest.main()