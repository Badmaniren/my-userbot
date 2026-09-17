import unittest
import uuid
import time
from skills.system_telemetry_streamer import stream_system_health_telemetry, SystemTelemetryStreamer
from skills.system_health_aggregator import aggregate_system_health
from skills.system_health_telemetry_collector import collect_telemetry_metrics

class TestSystemTelemetryStreamerIntegration(unittest.TestCase):
    def test_stream_system_health_telemetry_integration(self):
        random_run_id = str(uuid.uuid4())
        random_metric_value = uuid.uuid4().hex

        input_health_data = {
            "run_id": random_run_id,
            "status": "active",
            "metric_payload": random_metric_value,
            "timestamp": time.time()
        }

        aggregated = aggregate_system_health(input_health_data)

        result = stream_system_health_telemetry(aggregated)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("streamed"))
        self.assertEqual(result.get("processed_run_id"), random_run_id)
        self.assertIn("timestamp", result)

    def techno_streamer_execution_test(self):
        streamer = SystemTelemetryStreamer()
        random_stream_id = str(uuid.uuid4())

        try:
            streamer.stream_telemetry(stream_stream_id=random_stream_id)
        except NotImplementedError:
            pass

if __name__ == "__main__":
    unittest.main()