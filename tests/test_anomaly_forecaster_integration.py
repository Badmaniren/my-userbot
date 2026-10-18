import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_forecaster import AnomalyForecaster, ModelNotTrainedError, AnomalyForecasterError, ForecastResult, forecast_anomalies

class TestAnomalyForecasterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"test_log_{uuid.uuid4().hex}.json")
        self.report_file = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex}.json")
        self.logger = AnomalyLogger(log_path=self.log_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_forecaster_workflow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_val = random.randint(1, 100)
        metric_val = random.uniform(0.0, 1000.0)
        
        details_msg = f"Integration test anomaly message {uuid.uuid4()}"
        telemetry_data = {"cpu_load": metric_val, "active": True}

        self.logger.log_anomaly(
            source=source_id,
            severity=severity_val,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        forecaster = AnomalyForecaster(log_path=self.log_file, model_name=f"model_{uuid.uuid4().hex[:6]}", threshold=0.5)
        
        with self.assertRaises(ModelNotTrainedError):
            forecaster.predict(telemetry_data)

        forecaster.train()
        self.assertTrue(forecaster.is_trained)
        self.assertEqual(len(forecaster.historical_data), 1)

        prediction = forecaster.predict(telemetry_data)
        self.assertIsInstance(prediction, ForecastResult)
        self.assertTrue(prediction.is_anomaly)
        self.assertGreaterEqual(prediction.confidence_score, 0.5)
        self.assertEqual(prediction.telemetry_snapshot["cpu_load"], metric_val)

        forecaster.export_report([prediction], self.report_file)
        self.assertTrue(os.path.exists(self.report_file))
        
        with open(self.report_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(str(metric_val), content)

        stream_data = io_bytes = f"Raw stream data {uuid.uuid4()}".encode("utf-8")
        import io
        stream_io = io.BytesIO(io_bytes)
        parsed_stream = forecaster.parse_raw_stream(stream_io)
        self.assertIn("stream_hash", parsed_stream)
        self.assertEqual(parsed_stream["size"], len(io_bytes))

        forecast_func_result = forecast_anomalies(self.logger)
        self.assertIsInstance(forecast_func_result, str)
        self.assertIn("Forecasted anomalies report", forecast_func_result)

    def test_integration_empty_history_training(self):
        empty_forecaster = AnomalyForecaster(log_path=self.log_file)
        with self.assertRaises(AnomalyForecasterError):
            empty_forecaster.train()

    def test_integration_invalid_threshold(self):
        invalid_thresh = random.uniform(1.1, 10.0)
        with self.assertRaises(AnomalyForecasterError):
            AnomalyForecaster(log_path=self.log_file, threshold=invalid_thresh)

if __name__ == "__main__":
    unittest.main()