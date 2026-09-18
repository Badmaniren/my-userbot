import unittest
import uuid
import random
from skills.system_telemetry_streamer import SystemTelemetryStreamer, system_telemetry_streamer

class TestSystemTelemetryStreamerIntegration(unittest.TestCase):
    def test_system_telemetry_streamer_integration(self):
        test_session_id = str(uuid.uuid4())
        test_mode = random.choice(["realtime", "batch", "diagnostic"])

        result = system_telemetry_streamer(session_id=test_session_id, stream_mode=test_mode)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("session_id"), test_session_id)
        self.assertEqual(result.get("streaming_active"), True)
        self.assertIn("status", result)

    def test_system_telemetry_streamer_generator(self):
        streamer = SystemTelemetryStreamer(interval=0.01)
        stream_gen = streamer.stream()

        data_sample = next(stream_gen)
        self.assertIsInstance(data_sample, dict)

if __name__ == "__main__":
    unittest.main()