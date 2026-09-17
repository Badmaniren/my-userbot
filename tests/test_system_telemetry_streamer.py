import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import time
from skills.system_telemetry_streamer import SystemTelemetryStreamer, system_telemetry_streamer

class TestSystemTelemetryStreamer(unittest.TestCase):

    def setUp(self):
        self.streamer = SystemTelemetryStreamer()
        self.host_name = f"host-{uuid.uuid4().hex[:8]}"
        self.metric_name = f"metric-{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(0.0, 100.0), 2)
        self.endpoint_url = f"http://{uuid.uuid4().hex[:6]}.local/telemetry"

    def test_generate_payload(self):
        payload = self.streamer.generate_payload(self.metric_name, self.metric_value, self.host_name)

        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["metric_name"], self.metric_name)
        self.assertEqual(payload["value"], self.metric_value)
        self.assertEqual(payload["host"], self.host_name)
        self.assertIn("timestamp", payload)
        self.assertIsInstance(payload["timestamp"], float)

    @patch("skills.system_telemetry_streamer.requests.post")
    def test_stream_metric_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([200, 201, 202])
        mock_post.return_value = mock_response

        result = self.streamer.stream_metric(self.endpoint_url, self.metric_name, self.metric_value, self.host_name)

        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.endpoint_url)
        self.assertIn("json", kwargs)
        self.assertEqual(kwargs["json"]["metric_name"], self.metric_name)

    @patch("skills.system_telemetry_streamer.requests.post")
    def test_stream_metric_failure_status(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        mock_post.return_value = mock_response

        result = self.streamer.stream_metric(self.endpoint_url, self.metric_name, self.metric_value, self.host_name)

        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch("skills.system_telemetry_streamer.requests.post")
    def test_stream_metric_exception(self, mock_post):
        mock_post.side_effect = Exception(f"Network error {uuid.uuid4().hex[:4]}")

        result = self.streamer.stream_metric(self.endpoint_url, self.metric_name, self.metric_value, self.host_name)

        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch("skills.system_telemetry_streamer.requests.post")
    def test_stream_batch_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([200, 201, 202])
        mock_post.return_value = mock_response

        batch_size = random.randint(2, 5)
        batch = [
            self.streamer.generate_payload(f"m-{i}", float(i), self.host_name)
            for i in range(batch_size)
        ]

        result = self.streamer.stream_batch(self.endpoint_url, batch)

        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.endpoint_url)
        self.assertEqual(kwargs["json"], batch)

    @patch("skills.system_telemetry_streamer.requests.post")
    def test_stream_batch_failure_status(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 500, 503])
        mock_post.return_value = mock_response

        batch = [self.streamer.generate_payload(self.metric_name, self.metric_value, self.host_name)]

        result = self.streamer.stream_batch(self.endpoint_url, batch)

        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch("skills.system_telemetry_streamer.requests.post")
    def test_stream_batch_exception(self, mock_post):
        mock_post.side_effect = Exception(f"Timeout error {uuid.uuid4().hex[:4]}")

        batch = [self.streamer.generate_payload(self.metric_name, self.metric_value, self.host_name)]

        result = self.streamer.stream_batch(self.endpoint_url, batch)

        self.assertFalse(result)
        mock_post.assert_called_once()

    def test_system_telemetry_streamer_function_with_stream_id(self):
        custom_stream_id = f"stream-{uuid.uuid4().hex[:10]}"
        payload = {
            "stream_id": custom_stream_id,
            "data": uuid.uuid4().hex
        }

        response = system_telemetry_streamer(payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["stream_id"], custom_stream_id)
        self.assertIn("processed_at", response)
        self.assertIsInstance(response["processed_at"], float)

    def test_system_telemetry_streamer_function_default_stream_id(self):
        payload = {
            "metric": uuid.uuid4().hex
        }

        response = system_telemetry_streamer(payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["stream_id"], "default-stream")
        self.assertIn("processed_at", response)

if __name__ == "__main__":
    unittest.main()