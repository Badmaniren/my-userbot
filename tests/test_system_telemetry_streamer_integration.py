import unittest
import uuid
import random
import time
from skills.system_telemetry_streamer import system_telemetry_streamer
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.system_health_aggregator import system_health_aggregator

class TestSystemTelemetryStreamerIntegration(unittest.TestCase):
    def test_telemetry_streamer_real_integration(self):
        stream_id = str(uuid.uuid4())
        metric_sample_rate = random.randint(1, 10)

        collected_data = system_health_telemetry_collector(stream_id=stream_id, rate=metric_sample_rate)
        self.assertIsNotNone(collected_data)

        aggregated_health = system_health_aggregator(data=collected_data)
        self.assertIsInstance(aggregated_health, dict)

        stream_result = system_telemetry_streamer(
            stream_id=stream_id,
            telemetry_payload=aggregated_health,
            duration=1
        )

        self.assertIn("stream_id", stream_result)
        self.assertEqual(stream_result["stream_id"], stream_id)
        self.assertTrue(stream_result.get("status") in ["active", "streaming", "completed"])

if __name__ == "__main__":
    unittest.main()