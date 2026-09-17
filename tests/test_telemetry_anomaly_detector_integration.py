import unittest
import uuid
import random
import time
from skills.telemetry_anomaly_detector import TelemetryAnomalyDetector
from skills.telemetry_processor import TelemetryProcessor
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestTelemetryAnomalyDetectorIntegration(unittest.TestCase):
    def test_anomaly_detection_integration_real_flow(self):
        collector = SystemHealthTelemetryCollector()
        processor = TelemetryProcessor()
        detector = TelemetryAnomalyDetector()

        unique_metric_name = f"metric_cpu_load_{uuid.uuid4().hex[:8]}"
        random_spike_value = round(random.uniform(95.0, 150.0), 2)
        random_baseline_value = round(random.uniform(10.0, 40.0), 2)

        raw_telemetry = {
            "metric": unique_metric_name,
            "values": [random_baseline_value, random_baseline_value, random_spike_value],
            "timestamp": int(time.time())
        }

        collected_data = collector.collect(raw_telemetry)
        processed_stream = processor.process(collected_data)

        anomaly_result = detector.detect(processed_stream)

        self.assertIsInstance(anomaly_result, dict)
        self.assertIn("anomalies_detected", anomaly_result)
        self.assertTrue(anomaly_result["anomalies_detected"])
        self.assertIn(unique_metric_name, str(anomaly_result))

if __name__ == "__main__":
    unittest.main()