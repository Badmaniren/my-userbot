import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.system_telemetry_streamer import SystemTelemetryStreamer


class TestSystemTelemetryStreamer(unittest.TestCase):

    def setUp(self):
        self.streamer = SystemTelemetryStreamer()
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.random_metric_value = random.uniform(10.0, 999.9)
        self.random_host_id = uuid.uuid4().hex

    def test_stream_telemetry_payload_generation(self):
        metric_payload = {
            "host": self.random_host_id,
            "metric": self.random_metric_name,
            "value": self.random_metric_value
        }

        serialized_data = json.dumps(metric_payload)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = io.BytesIO(serialized_data.encode('utf-8')).read()

        with patch('requests.post', return_value=mock_response) as mock_post:
            target_url = f"http://{uuid.uuid4().hex}.local/telemetry"
            result = self.streamer.stream_metric(target_url, metric_payload)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], target_url)
            self.assertIn(self.random_host_id, kwargs['data'])
            self.assertTrue(result)

    def test_telemetry_stream_failure_handling(self):
        fail_payload = {
            "error_code": random.randint(500, 599),
            "trace_id": uuid.uuid4().hex
        }

        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = Exception("Service Unavailable")

        with patch('requests.post', return_value=mock_response) as mock_post:
            target_url = f"http://{uuid.uuid4().hex}.net/stream"
            result = self.streamer.stream_metric(target_url, fail_payload)

            mock_post.assert_called_once()
            self.assertFalse(result)

    def batch_telemetry_stream_aggregation(self):
        batch_size = random.randint(3, 10)
        batch_data = [
            {
                "uuid": uuid.uuid4().hex,
                "load": random.randint(1, 100)
            }
            for _ in range(batch_size)
        ]

        mock_stream = io.BytesIO(b'OK')

        with patch('requests.Session.post') as mock_session_post:
            mock_session_post.return_value.status_code = 202
            mock_session_post.return_value.raw = mock_stream

            endpoint = f"https://{uuid.uuid4().hex}.org/collect"
            status = self.streamer.stream_batch(endpoint, batch_data)

            self.assertTrue(status)
            mock_session_post.assert_called_once()
            called_kwargs = mock_session_post.call_args[1]
            self.assertIn('json', called_kwargs)
            self.assertEqual(len(called_kwargs['json']), batch_size)