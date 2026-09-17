import unittest
import uuid
import random
import os
from skills.telemetry_anomaly_detector_v2 import telemetry_anomaly_detector_v2
from skills.telemetry_processor import telemetry_processor
from skills.incident_aggregator import incident_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector

class TestIntegrationTelemetryAnomalyDetectorV2(unittest.TestCase):
    def test_anomaly_detector_integration_flow(self):
        unique_device_id = str(uuid.uuid4())
        metric_value = random.uniform(150.0, 500.0)

        telemetry_payload = {
            "device_id": unique_device_id,
            "metric": "processor_temperature",
            "value": metric_value,
            "status": "critical"
        }

        collector_result = system_health_telemetry_collector(telemetry_payload)
        self.assertIsNotNone(collector_result)

        processed_stream = telemetry_processor(collector_result)
        self.assertIsNotNone(processed_stream)

        detection_result = telemetry_anomaly_detector_v2(processed_stream)
        self.assertIsInstance(detection_result, dict)
        self.assertTrue(detection_result.get("anomaly_detected", False))

        incident_id = str(uuid.uuid4())
        incident_payload = {
            "incident_id": incident_id,
            "source": "telemetry_anomaly_detector_v2",
            "device_id": unique_device_id,
            "severity": "HIGH",
            "details": detection_result
        }

        aggregator_response = incident_aggregator(incident_payload)
        self.assertEqual(aggregator_response.get("status"), "recorded")
        self.assertEqual(aggregator_response.get("incident_id"), incident_id)

if __name__ == "__main__":
    unittest.main()