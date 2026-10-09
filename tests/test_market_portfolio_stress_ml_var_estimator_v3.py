import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import requests
except ImportError:
    requests = None

from skills.market_portfolio_stress_ml_var_estimator_v3 import (
    MLVaREstimatorV3,
    VaREestimationError,
    InsufficientDataError,
    market_portfolio_stress_ml_var_estimator_v3
)

class TestMarketPortfolioStressMLVaREstimatorV3(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.weights = [random.random(), random.random()]
        self.returns = [random.uniform(-0.05, 0.05) for _ in range(10)]
        self.confidence = random.choice([0.95, 0.99])
        self.horizon = random.choice([1, 5, 10])

    def test_ml_var_estimator_success(self):
        vol_forecaster = MagicMock()
        predicted_vol = random.uniform(0.1, 0.5)
        vol_forecaster.predict_volatility.return_value = predicted_vol

        mc_engine = MagicMock()
        tail_risk = random.uniform(1000.0, 50000.0)
        mc_engine.simulate_tail_risk.return_value = tail_risk

        db_storage = MagicMock()

        estimator = MLVaREstimatorV3(
            volatility_forecaster=vol_forecaster,
            monte_carlo_engine=mc_engine,
            db_storage=db_storage
        )

        result = estimator.calculate_var(
            portfolio_id=self.portfolio_id,
            weights=self.weights,
            returns=self.returns,
            confidence=self.confidence,
            horizon=self.horizon
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_value"], tail_risk)
        self.assertEqual(result["predicted_volatility"], predicted_vol)
        self.assertIn("timestamp", result)
        db_storage.save_estimate.assert_called_once()

    def test_ml_var_estimator_insufficient_data(self):
        estimator = MLVaREstimatorV3()
        short_returns = [random.uniform(-0.01, 0.01) for _ in range(3)]

        with self.assertRaises(InsufficientDataError):
            estimator.calculate_var(
                portfolio_id=self.portfolio_id,
                weights=self.weights,
                returns=short_returns,
                confidence=self.confidence,
                horizon=self.horizon
            )

    def test_ml_var_estimator_calculation_error(self):
        vol_forecaster = MagicMock()
        vol_forecaster.predict_volatility.side_effect = ValueError(uuid.uuid4().hex)

        estimator = MLVaREstimatorV3(volatility_forecaster=vol_forecaster)

        with self.assertRaises(VaREestimationError):
            estimator.calculate_var(
                portfolio_id=self.portfolio_id,
                weights=self.weights,
                returns=self.returns,
                confidence=self.confidence,
                horizon=self.horizon
            )

    def test_parse_external_market_stream(self):
        estimator = MLVaREstimatorV3()
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)

        res = estimator.parse_external_market_stream(stream)
        self.assertEqual(res, random_bytes)

    def test_fetch_external_benchmark(self):
        estimator = MLVaREstimatorV3()
        url = f"https://example.com/api/{uuid.uuid4().hex}"
        expected_json = {"metric": uuid.uuid4().hex}

        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = expected_json
        mock_requests.get.return_value = mock_response

        with patch("skills.market_portfolio_stress_ml_var_estimator_v3.requests", mock_requests):
            res = estimator.fetch_external_benchmark(url)
            self.assertEqual(res, expected_json)
            mock_requests.get.assert_called_once_with(url, timeout=10)

    def test_extract_anomaly_metric_found(self):
        estimator = MLVaREstimatorV3()
        class_name = f"cls_{uuid.uuid4().hex[:6]}"
        metric_value = uuid.uuid4().hex
        if BeautifulSoup is not None:
            html_content = f'<div class="{class_name}">{metric_value}</div>'
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            soup = MagicMock()
            mock_elem = MagicMock()
            mock_elem.text.strip.return_value = metric_value
            soup.find.return_value = mock_elem

        res = estimator.extract_anomaly_metric(soup, class_name)
        self.assertEqual(res, metric_value)

    def test_extract_anomaly_metric_not_found(self):
        estimator = MLVaREstimatorV3()
        class_name = f"cls_{uuid.uuid4().hex[:6]}"
        if BeautifulSoup is not None:
            soup = BeautifulSoup('<div></div>', 'html.parser')
        else:
            soup = MagicMock()
            soup.find.return_value = None

        res = estimator.extract_anomaly_metric(soup, class_name)
        self.assertIsNone(res)

    def test_functional_wrapper_handler(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence,
            "volatility_forecast": [0.1, 0.2, 0.3],
            "base_value": 200000.0
        }

        with patch("skills.db_storage.db_storage") as mock_db:
            result = market_portfolio_stress_ml_var_estimator_v3(payload)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("var_value", result)
            self.assertIn("predicted_volatility", result)
            self.assertEqual(result["predicted_volatility"], 0.2)
            mock_db.assert_called_once()

    def test_functional_wrapper_scalar_volatility(self):
        scalar_vol = random.uniform(0.05, 0.5)
        payload = {
            "portfolio_id": self.portfolio_id,
            "volatility_forecast": scalar_vol,
            "base_value": 50000.0
        }

        with patch("skills.db_storage.db_storage") as mock_db:
            result = market_portfolio_stress_ml_var_estimator_v3(payload)

            self.assertEqual(result["predicted_volatility"], scalar_vol)
            self.assertEqual(result["var_value"], 50000.0 * scalar_vol * 1.645)
            mock_db.assert_called_once()

if __name__ == '__main__':
    unittest.main()