import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import time

from skills.system_telemetry_streamer import (
    SystemTelemetryStreamer,
    StreamerConfigurationError,
    TelemetryStreamExecutionError
)

class TestSystemTelemetryStreamerArchitectInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_stream_id = uuid.uuid4().hex
        self.rand_endpoint = f"http://{uuid.uuid4().hex[:8]}.local/{uuid.uuid4().hex[:6]}"
        self.rand_interval = random.uniform(0.01, 1.0)
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_metric_value = random.randint(-100000, 100000)

    def test_streamer_initialization_with_random_config(self):
        streamer = SystemTelemetryStreamer(
            stream_id=self.rand_stream_id,
            destination_url=self.rand_endpoint,
            poll_interval=self.rand_interval
        )
        self.assertEqual(streamer.stream_id, self.rand_stream_id)
        self.assertEqual(streamer.destination_url, self.rand_endpoint)
        self.assertEqual(streamer.poll_interval, self.rand_interval)
        self.assertFalse(streamer.is_streaming)

    def test_streamer_invalid_interval_raises_error(self):
        bad_interval = -random.uniform(0.1, 100.0)
        with self.assertRaises((StreamerConfigurationError, ValueError)):
            SystemTelemetryStreamer(
                stream_id=uuid.uuid4().hex,
                destination_url=self.rand_endpoint,
                poll_interval=bad_interval
            )

    def test_collect_single_telemetry_metric(self):
        streamer = SystemTelemetryStreamer(
            stream_id=self.rand_stream_id,
            destination_url=self.rand_endpoint,
            poll_interval=self.rand_interval
        )

        mock_collector_output = {
            self.rand_metric_name: self.rand_metric_value,
            "timestamp": time.time(),
            "uuid": uuid.uuid4().hex
        }

        with patch('skills.system_telemetry_streamer.system_health_telemetry_collector') as mock_collector:
            mock_collector.gather.return_value = mock_collector_output

            result = streamer.collect_metric_batch()

            self.assertIn(self.rand_metric_name, result)
            self.assertEqual(result[self.rand_metric_name], self.rand_metric_value)
            mock_collector.gather.assert_called_once()

    def test_stream_transmission_via_network_mock(self):
        streamer = SystemTelemetryStreamer(
            stream_id=self.rand_stream_id,
            destination_url=self.rand_endpoint,
            poll_interval=self.rand_interval
        )

        payload_data = {
            "stream_uuid": self.rand_stream_id,
            "data": uuid.uuid4().hex,
            "val": random.random()
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "acknowledged", "token": uuid.uuid4().hex}

        with patch('requests.post', return_value=mock_response) as mock_post:
            resp = streamer.transmit_telemetry(payload_data)

            mock_post.assert_called_once_with(
                self.rand_endpoint,
                json=payload_data,
                timeout=unittest.mock.ANY
            )
            self.assertEqual(resp["status"], "acknowledged")

    def test_stream_transmission_network_failure_handling(self):
        streamer = SystemTelemetryStreamer(
            stream_id=self.rand_stream_id,
            destination_url=self.rand_endpoint,
            poll_interval=self.rand_interval
        )

        payload_data = {
            "error_test_id": uuid.uuid4().hex
        }

        with patch('requests.post', side_effect=Exception(uuid.uuid4().hex)) as mock_post:
            with self.assertRaises((TelemetryStreamExecutionError, ConnectionError, Exception)):
                streamer.transmit_telemetry(payload_data)
            mock_post.assert_called_once()

    def test_stream_consumer_bytes_io_integration(self):
        streamer = SystemTelemetryStreamer(
            stream_id=self.rand_stream_id,
            destination_url=self.rand_endpoint,
            poll_interval=self.rand_interval
        )

        stream_content = f"telemetry_stream_{uuid.uuid4().hex}"
        mock_stream_buffer = io.BytesIO(stream_content.encode('utf-8'))

        processed_data = streamer.process_raw_byte_stream(mock_stream_buffer)

        self.assertEqual(processed_data.get("raw_text"), stream_content)
        self.assertTrue(len(processed_data.get("raw_bytes", b"")) > 0)

    def test_streaming_lifecycle_execution(self):
        streamer = SystemTelemetryStreamer(
            stream_id=self.rand_stream_id,
            destination_url=self.rand_endpoint,
            poll_interval=0.01
        )

        with patch.object(streamer, 'collect_metric_batch', return_value={uuid.uuid4().hex: random.randint(0, 100)}) as mock_collect, \
             patch.object(streamer, 'transmit_telemetry', return_value={"status": "ok"}) as mock_transmit:

            streamer.start_streaming_cycle(max_iterations=2)

            self.assertEqual(mock_collect.call_count, 2)
            self.assertEqual(mock_transmit.call_count, 2)

if __name__ == '__main__':
    unittest.main()