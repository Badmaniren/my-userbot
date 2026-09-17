import unittest
from unittest.mock import patch
import random
import uuid
import time
from skills.system_telemetry_streamer import SystemTelemetryStreamer, system_telemetry_streamer

class TestSystemTelemetryStreamer(unittest.TestCase):
    def test_system_telemetry_streamer_class_iteration(self):
        rand_interval = round(random.uniform(0.01, 0.1), 3)
        rand_status = uuid.uuid4().hex
        rand_cpu = random.randint(10, 99)

        mock_data = {"status": rand_status, "cpu_usage": rand_cpu}

        streamer = SystemTelemetryStreamer(interval=rand_interval)

        with patch("skills.system_telemetry_streamer.system_health_telemetry_collector") as mock_collector:
            mock_collector.collect.return_value = mock_data

            generator = streamer.stream()
            first_item = next(generator)

            self.assertEqual(first_item, mock_data)
            self.assertEqual(first_item["status"], rand_status)
            self.assertEqual(first_item["cpu_usage"], rand_cpu)

    def test_system_telemetry_streamer_function_with_dict(self):
        rand_session = uuid.uuid4().hex
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        rand_mode = uuid.uuid4().hex

        initial_data = {rand_key: rand_val, "status": "active"}

        with patch("skills.system_telemetry_streamer.system_health_telemetry_collector") as mock_collector_func:
            mock_collector_func.return_value = initial_data

            result = system_telemetry_streamer(session_id=rand_session, stream_mode=rand_mode)

            self.assertIsInstance(result, dict)
            self.assertEqual(result[rand_key], rand_val)
            self.assertEqual(result["status"], "active")
            self.assertEqual(result["session_id"], rand_session)
            self.assertTrue(result["streaming_active"])

    def test_system_telemetry_streamer_function_non_dict_fallback(self):
        rand_session = uuid.uuid4().hex
        rand_mode = uuid.uuid4().hex

        with patch("skills.system_telemetry_streamer.system_health_telemetry_collector") as mock_collector_func:
            mock_collector_func.return_value = [uuid.uuid4().hex, random.randint(1, 100)]

            result = system_telemetry_streamer(session_id=rand_session, stream_mode=rand_mode)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["status"], "nominal")
            self.assertEqual(result["session_id"], rand_session)
            self.assertTrue(result["streaming_active"])

    def test_system_telemetry_streamer_function_missing_status(self):
        rand_session = uuid.uuid4().hex
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        initial_data = {rand_key: rand_val}

        with patch("skills.system_telemetry_streamer.system_health_telemetry_collector") as mock_collector_func:
            mock_collector_func.return_value = initial_data

            result = system_telemetry_streamer(session_id=rand_session)

            self.assertEqual(result["status"], "nominal")
            self.assertEqual(result[rand_key], rand_val)
            self.assertEqual(result["session_id"], rand_session)
            self.assertTrue(result["streaming_active"])

if __name__ == "__main__":
    unittest.main()