import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.telemetry_streamer import (
    TelemetryStreamer,
    StreamAggregationEngine,
    PipelineConnector
)

class TestTelemetryStreamerArchitecturalCompliance(unittest.TestCase):

    def setUp(self):
        self.stream_id = uuid.uuid4().hex
        self.endpoint_url = f"https://telemetry.{uuid.uuid4().hex}.internal/v1/stream"
        self.buffer_size = random.randint(1024, 65535)
        self.streamer = TelemetryStreamer(stream_id=self.stream_id, endpoint=self.endpoint_url, buffer_size=self.buffer_size)

    def test_telemetry_streamer_initialization(self):
        self.assertEqual(self.streamer.stream_id, self.stream_id)
        self.assertEqual(self.streamer.endpoint, self.endpoint_url)
        self.assertEqual(self.streamer.buffer_size, self.buffer_size)
        self.assertFalse(self.streamer.is_streaming)

    def test_aggregate_and_push_raw_health_telemetry(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        metric_value = random.uniform(0.1, 999.9)
        timestamp = random.randint(1600000000, 1700000000)
        
        payload_data = {
            "metric": metric_name,
            "value": metric_value,
            "timestamp": timestamp,
            "uuid": uuid.uuid4().hex
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "accepted", "ack_id": uuid.uuid4().hex}

        with patch("requests.post") as mock_post:
            mock_post.return_value = mock_response
            
            result = self.streamer.push_telemetry(payload_data)
            
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(self.endpoint_url, args)
            self.assertTrue(result)
            self.assertEqual(mock_post.call_count, 1)

    def test_stream_processor_buffer_overflow_handling(self):
        garbage_stream = io.BytesIO(uuid.uuid4().bytes * random.randint(5, 20))
        engine = StreamAggregationEngine(source_stream=garbage_stream, max_chunk=self.buffer_size)
        
        aggregated_chunks = list(engine.stream_chunks())
        self.assertGreater(len(aggregated_chunks), 0)
        for chunk in aggregated_chunks:
            self.assertIsInstance(chunk, bytes)

    def test_pipeline_connector_failure_recovery(self):
        connector = PipelineConnector(pipeline_url=self.endpoint_url)
        payload_key = uuid.uuid4().hex
        payload_val = uuid.uuid4().hex

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [Exception("Network partition"), MagicMock(status_code=201)]
            
            success = connector.transmit_with_retry({payload_key: payload_val}, retries=2)
            
            self.assertTrue(success)
            self.assertEqual(mock_post.call_count, 2)

    def test_telemetry_streamer_data_integrity(self):
        unique_marker = uuid.uuid4().hex
        raw_stream_data = f"HEADER:{unique_marker}\nBODY:{uuid.uuid4().hex}".encode('utf-8')
        mock_file_stream = io.BytesIO(raw_stream_data)

        with patch("skills.telemetry_streamer.open", return_value=mock_file_stream, create=True):
            read_data = self.streamer.read_from_source(uuid.uuid4().hex)
            self.assertIn(unique_marker.encode('utf-8'), read_data)

if __name__ == "__main__":
    unittest.main()