import sys
import types
import unittest
from unittest.mock import MagicMock, patch
import math
import random
import uuid
import string

if "requests" not in sys.modules:
    try:
        import requests
    except ModuleNotFoundError:
        sys.modules["requests"] = MagicMock()

# Инквизиторское решение: виртуальный stub для numpy в sys.modules,
# если зависимость отсутствует в окружении запуска (ModuleNotFoundError: No module named 'numpy').
if "numpy" not in sys.modules:
    try:
        import numpy as np
    except ModuleNotFoundError:
        np_mock = types.ModuleType("numpy")

        class MockNDArray(list):
            def __sub__(self, other):
                if isinstance(other, (int, float)):
                    return MockNDArray([x - other for x in self])
                return MockNDArray([x - y for x, y in zip(self, other)])

            def __pow__(self, power):
                return MockNDArray([x ** power for x in self])

        def _array(data):
            return MockNDArray(data)

        def _std(a, ddof=0):
            lst = list(a)
            n = len(lst)
            if n - ddof <= 0:
                return 0.0
            mean_val = sum(lst) / n
            var_val = sum((x - mean_val) ** 2 for x in lst) / (n - ddof)
            return math.sqrt(max(0.0, var_val))

        def _mean(a):
            lst = list(a)
            return sum(lst) / len(lst) if lst else 0.0

        def _sum(a):
            return sum(list(a))

        def _sort(a):
            return MockNDArray(sorted(list(a)))

        np_mock.array = _array
        np_mock.std = _std
        np_mock.mean = _mean
        np_mock.sum = _sum
        np_mock.sort = _sort
        sys.modules["numpy"] = np_mock

from skills.market_portfolio_ml_feature_builder import (
    FeatureBuilderConfigError,
    InsufficientDataError,
    MarketPortfolioMLFeatureBuilder,
    build_ml_features,
)


class TestMarketPortfolioMLFeatureBuilder(unittest.TestCase):
    def _random_str(self, prefix: str = "asset_") -> str:
        return f"{prefix}{uuid.uuid4().hex[:8]}"

    def _random_url(self) -> str:
        domain = "".join(random.choices(string.ascii_lowercase, k=8))
        path = uuid.uuid4().hex
        return f"https://{domain}.test/{path}.csv"

    def test_init_invalid_window_raises(self):
        asset_id = self._random_str()
        invalid_window = random.choice([0, 1, -1, -random.randint(2, 50)])
        with self.assertRaises(FeatureBuilderConfigError):
            MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=invalid_window)

    def test_init_valid_window(self):
        asset_id = self._random_str()
        window_size = random.randint(2, 30)
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=window_size)
        self.assertEqual(builder.asset_id, asset_id)
        self.assertEqual(builder.window_size, window_size)

    def test_compute_log_returns_insufficient_data(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=random.randint(2, 5))
        
        with self.assertRaises(InsufficientDataError):
            builder.compute_log_returns([])

        with self.assertRaises(InsufficientDataError):
            builder.compute_log_returns([random.uniform(10.0, 50.0)])

        with self.assertRaises(InsufficientDataError):
            builder.compute_log_returns(None)

    def test_compute_log_returns_with_zero_or_negative(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=random.randint(2, 5))
        p1 = random.uniform(10.0, 50.0)
        p2 = random.choice([0.0, -random.uniform(1.0, 10.0)])
        p3 = random.uniform(50.0, 100.0)
        prices = [p1, p2, p3]
        
        returns = builder.compute_log_returns(prices)
        self.assertEqual(len(returns), 2)
        self.assertEqual(returns[0], 0.0)
        self.assertEqual(returns[1], 0.0)

    def test_compute_log_returns_precise_math(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=random.randint(2, 5))
        prices = [random.uniform(10.0, 500.0) for _ in range(random.randint(3, 8))]
        expected = [math.log(prices[i + 1] / prices[i]) for i in range(len(prices) - 1)]
        
        actual = builder.compute_log_returns(prices)
        self.assertEqual(len(actual), len(expected))
        for act, exp in zip(actual, expected):
            self.assertAlmostEqual(act, exp, places=6)

    def test_compute_rolling_volatility_delegates_to_fetch_prices_if_none(self):
        asset_id = self._random_str()
        window = random.randint(2, 4)
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=window)
        dummy_prices = [random.uniform(50.0, 150.0) for _ in range(window + 3)]

        with patch.object(builder, "_fetch_historical_prices", return_value=dummy_prices) as mock_fetch:
            vols = builder.compute_rolling_volatility(None)
            mock_fetch.assert_called_once()
            self.assertTrue(len(vols) > 0)

    def test_compute_rolling_volatility_varying_lengths(self):
        asset_id = self._random_str()
        window = 3
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=window)
        
        # Test returns shorter than window
        short_returns = [random.uniform(-0.05, 0.05) for _ in range(2)]
        vols_short = builder.compute_rolling_volatility(short_returns)
        self.assertEqual(len(vols_short), 1)

        # Test empty returns
        vols_empty = builder.compute_rolling_volatility([])
        self.assertEqual(vols_empty, [])

        # Test normal window
        long_returns = [random.uniform(-0.05, 0.05) for _ in range(6)]
        vols_long = builder.compute_rolling_volatility(long_returns)
        expected_len = len(long_returns) - window + 1
        self.assertEqual(len(vols_long), expected_len)

    def test_compute_skewness_and_kurtosis_insufficient_or_constant(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=random.randint(2, 5))
        
        res_empty = builder.compute_skewness_and_kurtosis([])
        self.assertEqual(res_empty, {'skewness': 0.0, 'kurtosis': 0.0})

        res_two = builder.compute_skewness_and_kurtosis([random.uniform(0.1, 0.5), random.uniform(0.1, 0.5)])
        self.assertEqual(res_two, {'skewness': 0.0, 'kurtosis': 0.0})

        const_val = random.uniform(1.0, 10.0)
        res_const = builder.compute_skewness_and_kurtosis([const_val, const_val, const_val, const_val])
        self.assertEqual(res_const, {'skewness': 0.0, 'kurtosis': 0.0})

    def test_compute_skewness_and_kurtosis_calculation(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=3)
        returns = [random.uniform(-0.1, 0.1) for _ in range(10)]
        
        res = builder.compute_skewness_and_kurtosis(returns)
        self.assertIn('skewness', res)
        self.assertIn('kurtosis', res)
        self.assertIsInstance(res['skewness'], float)
        self.assertIsInstance(res['kurtosis'], float)

    def test_compute_tail_risk_metrics_empty(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=3)
        res = builder.compute_tail_risk_metrics([])
        self.assertEqual(res, {'var': 0.0, 'cvar': 0.0})

    def test_compute_tail_risk_metrics_values(self):
        asset_id = self._random_str()
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=3)
        returns = [random.uniform(-0.2, 0.2) for _ in range(20)]
        conf = random.choice([0.90, 0.95, 0.99])
        
        res = builder.compute_tail_risk_metrics(returns, confidence=conf)
        self.assertIn('var', res)
        self.assertIn('cvar', res)
        self.assertTrue(res['cvar'] <= res['var'] + 1e-6)

    def test_build_full_feature_vector_from_source_parsing_and_fallback(self):
        asset_id = self._random_str()
        window_size = random.randint(2, 5)
        builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=window_size)
        test_url = self._random_url()

        # Case 1: Valid CSV content
        mock_response_valid = MagicMock()
        val1, val2, val3, val4 = [random.uniform(50.0, 150.0) for _ in range(4)]
        mock_response_valid.content = f"noise,header\n{val1},{val2}\ninvalid,{val3}\n{val4}".encode('utf-8')

        with patch("requests.get", return_value=mock_response_valid) as mock_get:
            features = builder.build_full_feature_vector_from_source(test_url)
            mock_get.assert_called_with(test_url)
            self.assertEqual(features['asset_id'], asset_id)
            self.assertEqual(len(features['log_returns']), 3)
            self.assertIn('volatility', features)
            self.assertIn('rolling_volatility', features)
            self.assertIn('skewness', features)
            self.assertIn('kurtosis', features)
            self.assertIn('var', features)
            self.assertIn('cvar', features)

        # Case 2: Insufficient CSV parsed content triggering synthetic fallback
        mock_response_empty = MagicMock()
        mock_response_empty.content = b"only,strings,here\nno,numbers,found"

        with patch("requests.get", return_value=mock_response_empty) as mock_get:
            fallback_features = builder.build_full_feature_vector_from_source(test_url)
            mock_get.assert_called_with(test_url)
            self.assertEqual(fallback_features['asset_id'], asset_id)
            self.assertEqual(len(fallback_features['log_returns']), window_size + 4)

    def test_build_ml_features_function(self):
        asset_id = self._random_str()
        window_size = random.randint(2, 5)
        seed_marker = random.randint(1000, 999999)
        prices = [random.uniform(10.0, 100.0) for _ in range(window_size + 5)]

        result = build_ml_features(
            asset_id=asset_id,
            data_points=prices,
            window_size=window_size,
            seed_marker=seed_marker
        )

        self.assertEqual(result["asset_id"], asset_id)
        self.assertEqual(result["metadata"]["seed_marker"], seed_marker)
        self.assertEqual(len(result["log_returns"]), len(prices) - 1)
        self.assertIn("rolling_volatility", result)
        self.assertIn("skewness", result)
        self.assertIn("kurtosis", result)
        self.assertIn("tail_risk_metrics", result)
        self.assertIn("var", result["tail_risk_metrics"])
        self.assertIn("cvar", result["tail_risk_metrics"])


if __name__ == "__main__":
    unittest.main()