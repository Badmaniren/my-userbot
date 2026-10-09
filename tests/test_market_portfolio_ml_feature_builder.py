import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import math

from skills.market_portfolio_ml_feature_builder import (
    MarketPortfolioMLFeatureBuilder,
    FeatureBuilderConfigError,
    InsufficientDataError
)

class TestMarketPortfolioMLFeatureBuilder(unittest.TestCase):

    def setUp(self):
        self.asset_id = uuid.uuid4().hex
        self.window_size = random.randint(5, 30)
        self.builder = MarketPortfolioMLFeatureBuilder(
            asset_id=self.asset_id,
            window_size=self.window_size
        )

    def test_initialization_valid(self):
        rand_id = uuid.uuid4().hex
        rand_window = random.randint(10, 50)
        builder = MarketPortfolioMLFeatureBuilder(asset_id=rand_id, window_size=rand_window)
        self.assertEqual(builder.asset_id, rand_id)
        self.assertEqual(builder.window_size, rand_window)

    def test_initialization_invalid_window(self):
        rand_id = uuid.uuid4().hex
        invalid_window = random.randint(-10, 1)
        with self.assertRaises(FeatureBuilderConfigError):
            MarketPortfolioMLFeatureBuilder(asset_id=rand_id, window_size=invalid_window)

    def test_compute_log_returns_success(self):
        prices = [round(random.uniform(10.0, 1000.0), 4) for _ in range(self.window_size + 5)]
        
        with patch.object(self.builder, '_fetch_historical_prices', return_value=prices):
            returns = self.builder.compute_log_returns()
            self.assertIsInstance(returns, list)
            self.assertEqual(len(returns), len(prices) - 1)
            
            # Verify mathematical correctness of a random point
            idx = random.randint(0, len(returns) - 1)
            expected = math.log(prices[idx + 1] / prices[idx])
            self.assertAlmostEqual(returns[idx], expected, places=7)

    def test_compute_log_returns_insufficient_data(self):
        prices = [round(random.uniform(1.0, 10.0), 2)]
        with patch.object(self.builder, '_fetch_historical_prices', return_value=prices):
            with self.assertRaises(InsufficientDataError):
                self.builder.compute_log_returns()

    def test_compute_rolling_volatility(self):
        returns = [random.gauss(0, 0.02) for _ in range(self.window_size + 10)]
        with patch.object(self.builder, 'compute_log_returns', return_value=returns):
            vol = self.builder.compute_rolling_volatility()
            self.assertIsInstance(vol, list)
            self.assertGreater(len(vol), 0)
            for v in vol:
                self.assertGreaterEqual(v, 0.0)

    def test_compute_skewness_and_kurtosis(self):
        returns = [random.gauss(0.001, 0.03) for _ in range(self.window_size * 2)]
        with patch.object(self.builder, 'compute_log_returns', return_value=returns):
            metrics = self.builder.compute_skewness_and_kurtosis()
            self.assertIn('skewness', metrics)
            self.assertIn('kurtosis', metrics)
            self.assertIsInstance(metrics['skewness'], float)
            self.assertIsInstance(metrics['kurtosis'], float)

    def test_compute_tail_risk_metrics(self):
        returns = [random.gauss(-0.002, 0.04) for _ in range(self.window_size * 2)]
        confidence_level = round(random.uniform(0.90, 0.99), 2)
        
        with patch.object(self.builder, 'compute_log_returns', return_value=returns):
            tail_risks = self.builder.compute_tail_risk_metrics(confidence=confidence_level)
            self.assertIn('var', tail_risks)
            self.assertIn('cvar', tail_risks)
            self.assertLessEqual(tail_risks['var'], 0.0)
            self.assertLessEqual(tail_risks['cvar'], tail_risks['var'])

    def test_build_full_feature_vector_stream(self):
        random_bytes_len = random.randint(100, 500)
        mock_csv_data = "".join(random.choices(string.ascii_letters + string.digits + ",\n.", k=random_bytes_len))
        
        mock_file = io.BytesIO(mock_csv_data.encode('utf-8'))
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_file.read()
            mock_get.return_value = mock_response
            
            url_path = f"https://datastore.internal/{uuid.uuid4().hex}/prices.csv"
            features = self.builder.build_full_feature_vector_from_source(url_path)
            
            self.assertIsInstance(features, dict)
            self.assertEqual(features.get('asset_id'), self.asset_id)
            self.assertIn('volatility', features)
            self.assertIn('skewness', features)
            self.assertIn('kurtosis', features)
            self.assertIn('var', features)

if __name__ == '__main__':
    unittest.main()