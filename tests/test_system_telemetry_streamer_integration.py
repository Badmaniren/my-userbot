import unittest
import uuid
import random
import time
from skills.system_telemetry_streamer import SystemTelemetryStreamer, system_telemetry_streamer
from skills.system_health_aggregator import system_health_aggregator

class TestSystemTelemetryStreamerIntegration(unittest.TestCase):
    def setUp(self):
        self.streamer = SystemTelemetryStreamer()
        self.metric_name = f"cpu_load_{uuid.uuid4().hex[:8]}"
        self.value = round(random.uniform(10.0, 99.9), 2)
        self.host = f"host-{random.randint(100, 999)}.local"
        self.stream_id = f"stream-{uuid.uuid4()}"

    def test_payload_generation_and_pipeline_integration(self):
        payload = self.streamer.generate_payload(self.metric_name, self.value, self.host)

        self.assertIn("metric_name", payload)
        self.assertIn("value", payload)
        self.assertIn("host", payload)
        self.assertIn("timestamp", payload)

        self.assertEqual(payload["metric_name"], self.metric_name)
        self.assertEqual(payload["value"], self.value)
        self.assertEqual(payload["host"], self.host)

        extended_payload = {
            "stream_id": self.stream_id,
            "metric_data": payload
        }

        result = system_telemetry_streamer(extended_payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("stream_id"), self.stream_id)
        self.assertIn("processed_at", result)

        health_payload = {
            "stream_id": self.stream_id,
            "telemetry_status": result.get("status"),
            "metric": self.metric_name,
            "value": self.value
        }
        health_result = system_health_aggregator(health_payload)
        self.assertIsInstance(health_result, dict)

if __name__ == "__main__":
    unittest.main()