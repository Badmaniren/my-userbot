import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
from skills.anomaly_forecaster import (
    AnomalyForecasterError,
    ModelNotTrainedError,
    ForecastResult,
    AnomalyForecaster,
    forecast_anomalies
)
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyForecaster(unittest.TestCase):

    def test_forecast_result_str_and_init(self):
        is_anomaly = random.choice([True, False])
        confidence_score = random.uniform(0.0, 1.0)
        telemetry_snapshot = {uuid.uuid4().hex: uuid.uuid4().hex}

        res = ForecastResult(
            is_anomaly=is_anomaly,
            confidence_score=confidence_score,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertEqual(res.is_anomaly, is_anomaly)
        self.assertEqual(res.confidence_score, confidence_score)
        self.assertEqual(res.telemetry_snapshot, telemetry_snapshot)
        self.assertIn(str(is_anomaly), str(res))
        self.assertIn(str(confidence_score), str(res))

    def test_forecaster_init_invalid_threshold(self):
        log_path = f"{uuid.uuid4().hex}.log"
        bad_thresholds = [random.uniform(-10.0, -0.0001), random.uniform(1.0001, 10.0)]
        for threshold in bad_thresholds:
            with self.assertRaises(AnomalyForecasterError):
                AnomalyForecaster(log_path=log_path, threshold=threshold)

    def test_forecaster_train_empty_history(self):
        log_path = f"{uuid.uuid4().hex}.log"
        forecaster = AnomalyForecaster(log_path=log_path)

        with patch("skills.anomaly_forecaster.AnomalyLogger") as mock_logger_cls:
            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_anomalies.return_value = []

            with self.assertRaises(AnomalyForecasterError):
                forecaster.train()

    def test_forecaster_predict_not_trained(self):
        log_path = f"{uuid.uuid4().hex}.log"
        forecaster = AnomalyForecaster(log_path=log_path)
        telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}

        with self.assertRaises(ModelNotTrainedError):
            forecaster.predict(telemetry)

    def test_forecaster_train_and_predict_success(self):
        log_path = f"{uuid.uuid4().hex}.log"
        threshold = random.uniform(0.1, 0.9)
        forecaster = AnomalyForecaster(log_path=log_path, threshold=threshold)

        mock_history = [
            {"source": uuid.uuid4().hex, "severity": random.randint(1, 10), "telemetry": {uuid.uuid4().hex: uuid.uuid4().hex}}
        ]

        with patch("skills.anomaly_forecaster.AnomalyLogger") as mock_logger_cls:
            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_anomalies.return_value = mock_history

            forecaster.train()
            self.assertTrue(forecaster.is_trained)
            self.assertEqual(forecaster.historical_data, mock_history)

        test_telemetry = {uuid.uuid4().hex: random.randint(100, 999)}
        result = forecaster.predict(test_telemetry)

        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(result.telemetry_snapshot, test_telemetry)
        self.assertGreaterEqual(result.confidence_score, 0.0)

    def test_export_forecast_report(self):
        log_path = f"{uuid.uuid4().hex}.log"
        destination = f"{uuid.uuid4().hex}.json"
        forecaster = AnomalyForecaster(log_path=log_path)

        telemetry_key = uuid.uuid4().hex
        telemetry_val = uuid.uuid4().hex
        results = [
            ForecastResult(
                is_anomaly=True,
                confidence_score=0.88,
                telemetry_snapshot={telemetry_key: telemetry_val}
            )
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            forecaster.export_report(results, destination)
            mock_file.assert_called_once_with(destination, "w", encoding="utf-8")
            handle = mock_file()
            self.assertTrue(handle.write.called)

    def test_parse_raw_stream(self):
        log_path = f"{uuid.uuid4().hex}.log"
        forecaster = AnomalyForecaster(log_path=log_path)
        random_bytes = uuid.uuid4().bytes * 3
        stream = io.BytesIO(random_bytes)

        parsed = forecaster.parse_raw_stream(stream)

        self.assertIn("stream_hash", parsed)
        self.assertIn("size", parsed)
        self.assertIn("raw_preview", parsed)
        self.assertEqual(parsed["size"], len(random_bytes))
        self.assertEqual(parsed["raw_preview"], random_bytes[:50])

    def test_forecast_anomalies_helper(self):
        log_path = f"{uuid.uuid4().hex}.log"
        mock_logger = AnomalyLogger(log_path=log_path)

        source_name = uuid.uuid4().hex
        severity_val = random.randint(1, 5)

        with patch.object(AnomalyLogger, "get_anomalies", return_value=[{"source": source_name, "severity": severity_val}]), \
             patch.object(AnomalyLogger, "get_structured_report", return_value=uuid.uuid4().hex):
            
            response = forecast_anomalies(mock_logger)
            self.assertIsInstance(response, str)
            self.assertIn("Forecasted anomalies report", response)

    def test_forecast_anomalies_helper_with_telemetry(self):
        log_path = f"{uuid.uuid4().hex}.log"
        mock_logger = AnomalyLogger(log_path=log_path)

        tel_key = uuid.uuid4().hex
        tel_val = uuid.uuid4().hex
        anomaly_item = {
            "source": uuid.uuid4().hex,
            "severity": random.randint(1, 10),
            "telemetry": {tel_key: tel_val}
        }

        with patch.object(AnomalyLogger, "get_anomalies", return_value=[anomaly_item]), \
             patch.object(AnomalyLogger, "get_structured_report", return_value=uuid.uuid4().hex):
            
            response = forecast_anomalies(mock_logger)
            self.assertIsInstance(response, str)