import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json

from skills.incident_recovery_time_estimator import IncidentRecoveryTimeEstimator, estimate_recovery_time

class TestIncidentRecoveryTimeEstimator(unittest.TestCase):
    def setUp(self):
        self.estimator = IncidentRecoveryTimeEstimator()
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_fetch_historical_data_success(self):
        rand_duration = round(random.uniform(1.0, 50.0), 2)
        mock_data = [{"duration_hours": rand_duration}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = io.BytesIO(json.dumps(mock_data).encode("utf-8"))

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.estimator._fetch_historical_data(self.severity)
            mock_get.assert_called_once()
            self.assertEqual(result, mock_data)

    def test_fetch_historical_data_single_dict(self):
        rand_duration = round(random.uniform(1.0, 50.0), 2)
        mock_data = {"duration_hours": rand_duration}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = io.BytesIO(json.dumps(mock_data).encode("utf-8"))

        with patch("requests.get", return_value=mock_response):
            result = self.estimator._fetch_historical_data(self.severity)
            self.assertEqual(result, [mock_data])

    def test_fetch_historical_data_failure_status(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("requests.get", return_value=mock_response):
            result = self.estimator._fetch_historical_data(self.severity)
            self.assertEqual(result, [])

    def test_get_current_system_load_success(self):
        rand_val = round(random.uniform(10.0, 90.0), 2)
        metric_line = f"load={rand_val}\n".encode("ascii")
        mock_stream = io.BytesIO(metric_line)

        with patch("skills.system_health_telemetry_collector.stream_metrics", return_value=mock_stream):
            val = self.estimator._get_current_system_load()
            self.assertEqual(val, rand_val)

    def test_get_current_system_load_default(self):
        with patch("skills.system_health_telemetry_collector.stream_metrics", return_value=None):
            val = self.estimator._get_current_system_load()
            self.assertEqual(val, 50.0)

    def test_calculate_confidence_bounds(self):
        conf_low = self.estimator._calculate_confidence(0, 100.0)
        self.assertAlmostEqual(conf_low, 0.01)

        conf_high = self.estimator._calculate_confidence(100, 0.0)
        self.assertAlmostEqual(conf_high, 1.0)

    def test_estimate_with_empty_history(self):
        with patch.object(self.estimator, "_fetch_historical_data", return_value=[]):
            res = self.estimator.estimate(self.incident_id, self.severity)
            self.assertEqual(res["estimated_hours"], 24.0)
            self.assertEqual(res["confidence_score"], 0.1)

    def test_estimate_with_valid_history(self):
        rand_dur = round(random.uniform(5.0, 15.0), 2)
        history = [{"duration_hours": rand_dur}]
        rand_load = round(random.uniform(20.0, 60.0), 2)

        with patch.object(self.estimator, "_fetch_historical_data", return_value=history), \
             patch.object(self.estimator, "_get_current_system_load", return_value=rand_load):
            res = self.estimator.estimate(self.incident_id, self.severity)
            self.assertIn("estimated_hours", res)
            self.assertIn("confidence_score", res)
            self.assertGreater(res["estimated_hours"], 0.0)
            self.assertGreater(res["confidence_score"], 0.0)


class TestEstimateRecoveryTimeIntegration(unittest.TestCase):
    def test_estimate_recovery_time_with_dict(self):
        inc_id = str(uuid.uuid4())
        metric_val = round(random.uniform(10.0, 80.0), 2)
        aggregated = {
            "id": inc_id,
            "metric": metric_val
        }
        telemetry = {uuid.uuid4().hex: random.random()}

        result = estimate_recovery_time(aggregated, telemetry)
        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["estimated_minutes"], int(metric_val * 1.5))

    def test_estimate_recovery_time_fallback(self):
        aggregated = "not_a_dict"
        telemetry = None

        result = estimate_recovery_time(aggregated, telemetry)
        self.assertIn("incident_id", result)
        self.assertEqual(result["estimated_minutes"], 75)

    def test_estimate_recovery_time_zero_metric(self):
        inc_id = str(uuid.uuid4())
        aggregated = {
            "id": inc_id,
            "metric": 0.0
        }
        telemetry = {}

        result = estimate_recovery_time(aggregated, telemetry)
        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["estimated_minutes"], 30)


if __name__ == "__main__":
    unittest.main()