import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.anomaly_forecaster import (
    AnomalyForecaster,
    AnomalyForecasterError,
    ForecastResult,
    ModelNotTrainedError
)

class TestAnomalyForecaster(unittest.TestCase):

    def setUp(self):
        self.random_log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.random_model_name = f"model_{uuid.uuid4().hex[:8]}"
        self.random_threshold = random.uniform(0.1, 0.9)
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_source = f"source_{uuid.uuid4().hex[:6]}"
        self.random_details = f"Details {uuid.uuid4().hex}"
        self.random_telemetry = {uuid.uuid4().hex: random.randint(100, 999)}

    def test_forecaster_initialization_success(self):
        forecaster = AnomalyForecaster(
            log_path=self.random_log_path,
            model_name=self.random_model_name,
            threshold=self.random_threshold
        )
        self.assertEqual(forecaster.log_path, self.random_log_path)
        self.assertEqual(forecaster.model_name, self.random_model_name)
        self.assertEqual(forecaster.threshold, self.random_threshold)
        self.assertFalse(forecaster.is_trained)

    def test_forecaster_initialization_invalid_threshold(self):
        bad_threshold = random.choice([-1.5, 1.1, 5.0])
        with self.assertRaises(AnomalyForecasterError):
            AnomalyForecaster(
                log_path=self.random_log_path,
                threshold=bad_threshold
            )

    def test_train_model_with_historical_data(self):
        forecaster = AnomalyForecaster(log_path=self.random_log_path)
        
        mock_history = [
            {
                "source": self.random_source,
                "severity": self.random_severity,
                "details": self.random_details,
                "telemetry": self.random_telemetry,
                "timestamp": random.randint(1600000000, 1700000000)
            }
            for _ in range(random.randint(5, 15))
        ]

        with patch("skills.anomaly_forecaster.AnomalyLogger") as MockLogger:
            instance = MockLogger.return_value
            instance.get_anomalies.return_value = mock_history

            forecaster.train()

            self.assertTrue(forecaster.is_trained)
            instance.get_anomalies.assert_called_once()

    def test_train_model_empty_history_raises_error(self):
        forecaster = AnomalyForecaster(log_path=self.random_log_path)

        with patch("skills.anomaly_forecaster.AnomalyLogger") as MockLogger:
            instance = MockLogger.return_value
            instance.get_anomalies.return_value = []

            with self.assertRaises(AnomalyForecasterError):
                forecaster.train()
            self.assertFalse(forecaster.is_trained)

    def test_predict_anomaly_success(self):
        forecaster = AnomalyForecaster(
            log_path=self.random_log_path,
            threshold=0.5
        )
        forecaster.is_trained = True

        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.uniform(10.0, 100.0)
        input_telemetry = {random_metric_key: random_metric_val}

        with patch.object(forecaster, "_run_prediction_algorithm") as mock_algo:
            expected_score = random.uniform(0.6, 0.99)
            mock_algo.return_value = expected_score

            result = forecaster.predict(input_telemetry)

            self.assertIsInstance(result, ForecastResult)
            self.assertTrue(result.is_anomaly)
            self.assertEqual(result.confidence_score, expected_score)
            self.assertEqual(result.telemetry_snapshot, input_telemetry)

    def test_predict_anomaly_not_trained(self):
        forecaster = AnomalyForecaster(log_path=self.random_log_path)
        self.assertFalse(forecaster.is_trained)

        with self.assertRaises(ModelNotTrainedError):
            forecaster.predict({uuid.uuid4().hex: random.random()})

    def test_export_forecast_report(self):
        forecaster = AnomalyForecaster(log_path=self.random_log_path)
        
        mock_results = [
            ForecastResult(
                is_anomaly=random.choice([True, False]),
                confidence_score=random.uniform(0.0, 1.0),
                telemetry_snapshot={uuid.uuid4().hex: random.randint(1, 100)}
            )
            for _ in range(random.randint(2, 5))
        ]

        random_export_dest = f"/tmp/{uuid.uuid4().hex}.json"
        
        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            forecaster.export_report(mock_results, destination=random_export_dest)
            mock_file.assert_called_once_with(random_export_dest, "w", encoding="utf-8")
            
            handle = mock_file()
            self.assertTrue(handle.write.called)

    def test_io_stream_handling_simulation(self):
        forecaster = AnomalyForecaster(log_path=self.random_log_path)
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        processed_data = forecaster.parse_raw_stream(mock_stream)
        self.assertIsNotNone(processed_data)
        self.assertIn("stream_hash", processed_data)