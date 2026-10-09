import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
import requests

from skills.market_portfolio_stress_ml_var_estimator_v2 import (
    MarketPortfolioStressMLVaREstimatorV2,
    evaluate_portfolio_stress_ml_var
)


class TestMarketPortfolioStressMLVaREstimatorV2(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.9, 0.99), 4)
        self.horizon_days = random.randint(1, 30)
        self.export_id = f"exp_{uuid.uuid4().hex[:8]}"
        self.target_id = f"target_{uuid.uuid4().hex[:8]}"
        self.stream_url = f"https://{uuid.uuid4().hex[:6]}.com/stream"

        self.mock_db = MagicMock()
        self.mock_vol_forecaster = MagicMock()
        self.mock_monte_carlo = MagicMock()

        self.estimator = MarketPortfolioStressMLVaREstimatorV2(
            db_storage=self.mock_db,
            market_portfolio_stress_ml_volatility_forecaster_v2=self.mock_vol_forecaster,
            market_portfolio_stress_monte_carlo_engine=self.mock_monte_carlo
        )

    def test_estimate_var_success(self):
        expected_var_val = round(random.uniform(100.0, 50000.0), 2)
        self.mock_vol_forecaster.predict.return_value = round(random.uniform(0.1, 0.5), 4)
        self.mock_monte_carlo.simulate.return_value = {"var": expected_var_val}

        result = self.estimator.estimate_var(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_value"], expected_var_val)
        self.assertEqual(result["confidence_level"], self.confidence_level)
        self.assertEqual(result["horizon_days"], self.horizon_days)

        self.mock_vol_forecaster.predict.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            horizon_days=self.horizon_days
        )
        self.mock_monte_carlo.simulate.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days
        )

    def test_estimate_var_exception_handling(self):
        self.mock_vol_forecaster.predict.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(RuntimeError):
            self.estimator.estimate_var(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days
            )

    def test_process_external_stream(self):
        random_bytes = uuid.uuid4().bytes * random.randint(1, 5)
        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            length = self.estimator.process_external_stream(self.stream_url)
            mock_get.assert_called_once_with(self.stream_url, stream=True)
            self.assertEqual(length, len(random_bytes))

    def test_trigger_audit_export(self):
        expected_export_result = f"exported_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_portfolio_stress_ml_var_estimator_v2.market_portfolio_stress_audit_exporter_v2") as mock_exporter:
            mock_exporter.export.return_value = expected_export_result
            res = self.estimator.trigger_audit_export(self.export_id)
            self.assertEqual(res, expected_export_result)
            mock_exporter.export.assert_called_once_with(self.export_id)

    def test_check_market_anomalies(self):
        expected_analysis = {"anomaly_score": random.random(), "target_id": self.target_id}
        mock_detector = MagicMock()
        mock_detector.analyze.return_value = expected_analysis
        self.estimator.market_anomaly_detector = mock_detector

        res = self.estimator.check_market_anomalies(self.target_id)
        self.assertEqual(res, expected_analysis)
        mock_detector.analyze.assert_called_once_with(self.target_id)

    def test_evaluate_portfolio_stress_ml_var_without_mc(self):
        volatility = round(random.uniform(0.01, 0.99), 4)
        valuation = round(random.uniform(1000.0, 100000.0), 2)
        data = {
            "portfolio_id": self.portfolio_id,
            "volatility_forecast": volatility,
            "valuation": valuation
        }

        result = evaluate_portfolio_stress_ml_var(data)

        self.assertIsInstance(result, dict)
        self.assertIn("estimation_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        expected_var = float(valuation) * float(volatility) * 0.05
        self.assertEqual(result["var_value"], expected_var)

    def test_evaluate_portfolio_stress_ml_var_with_mc(self):
        volatility = round(random.uniform(0.01, 0.99), 4)
        valuation = round(random.uniform(1000.0, 100000.0), 2)
        mc_var = round(random.uniform(50.0, 5000.0), 2)
        data = {
            "portfolio_id": self.portfolio_id,
            "volatility_forecast": volatility,
            "valuation": valuation,
            "monte_carlo_results": {"var": mc_var}
        }

        result = evaluate_portfolio_stress_ml_var(data)

        self.assertIsInstance(result, dict)
        self.assertIn("estimation_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_value"], mc_var)


if __name__ == "__main__":
    unittest.main()