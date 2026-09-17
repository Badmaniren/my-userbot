import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
import requests
from skills.telemetry_streamer import (
    TelemetryStreamer,
    StreamAggregationEngine,
    PipelineConnector,
    SystemHealthTelemetryCollector,
    SystemHealthAggregator,
    SystemHealthAuditPipeline
)

class TestTelemetryStreamerSuite(unittest.TestCase):

    def setUp(self):
        self.stream_id = uuid.uuid4().hex
        self.endpoint = f"http://{uuid.uuid4().hex}.local/telemetry"
        self.buffer_size = random.choice([1024, 2048, 4096, 8192])

    def test_telemetry_streamer_push_success(self):
        streamer = TelemetryStreamer(stream_id=self.stream_id, endpoint=self.endpoint, buffer_size=self.buffer_size)
        payload = {"metric_id": uuid.uuid4().hex, "value": random.random()}

        with patch("skills.telemetry_streamer.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            result = streamer.push_telemetry(payload)
            self.assertTrue(result)
            mock_post.assert_called_once_with(self.endpoint, json=payload)

    def test_telemetry_streamer_push_no_endpoint(self):
        streamer = TelemetryStreamer(stream_id=self.stream_id, endpoint=None, buffer_size=self.buffer_size)
        payload = {"metric_id": uuid.uuid4().hex, "value": random.random()}
        
        result = streamer.push_telemetry(payload)
        self.assertFalse(result)

    def test_telemetry_streamer_read_from_source(self):
        streamer = TelemetryStreamer(stream_id=self.stream_id, endpoint=self.endpoint)
        file_path = f"/tmp/{uuid.uuid4().hex}.bin"
        file_content = uuid.uuid4().bytes

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            data = streamer.read_from_source(file_path)
            self.assertEqual(data, file_content)
            mock_file.assert_called_once_with(file_path, 'rb')

    def test_telemetry_streamer_process_and_push(self):
        streamer = TelemetryStreamer(stream_id=self.stream_id, endpoint=self.endpoint)
        corr_id = uuid.uuid4().hex
        packet = {"timestamp": corr_id, "data": random.randint(1, 100)}

        with patch("skills.telemetry_streamer.requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            res = streamer.process_and_push(packet)
            self.assertTrue(res["success"])
            self.assertEqual(res["correlation_id"], corr_id)
            mock_post.assert_called_once_with(self.endpoint, json=packet)

    def test_stream_aggregation_engine(self):
        raw_chunks = [uuid.uuid4().bytes for _ in range(3)]
        full_data = b"".join(raw_chunks)
        mock_source = io.BytesIO(full_data)
        
        chunk_size = random.choice([4, 8, 16])
        engine = StreamAggregationEngine(mock_source, max_chunk=chunk_size)
        
        collected = list(engine.stream_chunks())
        self.assertTrue(len(collected) > 0)
        self.assertEqual(b"".join(collected), full_data)

    def test_pipeline_connector_transmit_success(self):
        connector = PipelineConnector(pipeline_url=self.endpoint)
        payload = {"status": uuid.uuid4().hex}

        with patch("skills.telemetry_streamer.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            result = connector.transmit_with_retry(payload)
            self.assertTrue(result)

    def test_pipeline_connector_transmit_retry_then_success(self):
        connector = PipelineConnector(pipeline_url=self.endpoint)
        payload = {"status": uuid.uuid4().hex}

        with patch("skills.telemetry_streamer.requests.post") as mock_post:
            fail_resp = requests.Response()
            fail_resp.status_code = 500
            success_resp = requests.Response()
            success_resp.status_code = 201
            mock_post.side_effect = [fail_resp, success_resp]

            result = connector.transmit_with_retry(payload, retries=2)
            self.assertTrue(result)
            self.assertEqual(mock_post.call_count, 2)

    def test_pipeline_connector_transmit_fail_all(self):
        connector = PipelineConnector(pipeline_url=self.endpoint)
        payload = {"status": uuid.uuid4().hex}

        with patch("skills.telemetry_streamer.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Network error")

            result = connector.transmit_with_retry(payload, retries=1)
            self.assertFalse(result)

    def test_system_health_telemetry_collector_capture(self):
        collector = SystemHealthTelemetryCollector()
        raw_data = {"node": uuid.uuid4().hex, "cpu_load": random.uniform(0, 100)}
        
        # Fixing the attribute check to use existing standard methods if available,
        # or checking what capture actually does based on provided code.
        # The provided code says: return raw_data
        result = collector.capture(raw_data)
        self.assertEqual(result, raw_data)

    def test_system_health_aggregator(self):
        aggregator = SystemHealthAggregator()
        packet_1 = {"id": uuid.uuid4().hex, "metric": random.randint(1, 50)}
        packet_2 = {"id": uuid.uuid4().hex, "metric": random.randint(51, 100)}
        
        result = aggregator.aggregate([packet_1, packet_2])
        self.assertEqual(result, packet_1)

        empty_result = aggregator.aggregate([])
        self.assertEqual(empty_result, {})

    def test_system_health_audit_pipeline(self):
        pipeline = SystemHealthAuditPipeline()
        data = {"audit_id": uuid.uuid4().hex, "details": uuid.uuid4().hex}
        log_path = f"/var/log/{uuid.uuid4().hex}.json"

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = pipeline.log_to_audit(data, log_path)
            self.assertTrue(result)
            m_open.assert_called_once_with(log_path, 'w')
            handle = m_open()
            handle.write.assert_called()