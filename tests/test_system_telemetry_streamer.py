import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.system_telemetry_streamer import (
    SystemTelemetryStreamer,
    SystemHealthTelemetryCollector,
    SystemHealthMonitoringGateway,
    stream_system_health_telemetry
)


class TestSystemTelemetryStreamer(unittest.TestCase):

    def test_system_telemetry_streamer_success(self):
        stream_id = uuid.uuid4().hex
        random_bytes = uuid.uuid4().hex.encode('utf-8')

        mock_source = unittest.mock.MagicMock()
        mock_source.read.return_value = random_bytes

        with patch.object(SystemHealthTelemetryCollector, 'collect', return_value=mock_source) as mock_collect, \
             patch.object(SystemHealthMonitoringGateway, 'ingest', return_value=True) as mock_ingest:

            streamer = SystemTelemetryStreamer()
            result = streamer.stream_telemetry(stream_id)

            mock_collect.assert_called_once_with(stream_id)
            mock_source.read.assert_called_once()
            mock_ingest.assert_called_once_with(random_bytes)
            self.assertTrue(result)

    def test_system_telemetry_streamer_none_source(self):
        stream_id = uuid.uuid4().hex

        with patch.object(SystemHealthTelemetryCollector, 'collect', return_value=None) as mock_collect:
            streamer = SystemTelemetryStreamer()
            result = streamer.stream_telemetry(stream_id)

            mock_collect.assert_called_once_with(stream_id)
            self.assertIsNone(result)

    def test_system_telemetry_streamer_empty_data(self):
        stream_id = uuid.uuid4().hex

        mock_source = unittest.mock.MagicMock()
        mock_source.read.return_value = b""

        with patch.object(SystemHealthTelemetryCollector, 'collect', return_value=mock_source) as mock_collect, \
             patch.object(SystemHealthMonitoringGateway, 'ingest', return_value=True) as mock_ingest:

            streamer = SystemTelemetryStreamer()
            result = streamer.stream_telemetry(stream_id)

            mock_collect.assert_called_once_with(stream_id)
            mock_source.read.assert_called_once()
            mock_ingest.assert_called_once_with(b"")
            self.assertEqual(result, {})

    def test_system_telemetry_streamer_exception_propagation(self):
        stream_id = uuid.uuid4().hex
        error_message = uuid.uuid4().hex

        with patch.object(SystemHealthTelemetryCollector, 'collect', side_effect=Exception(error_message)) as mock_collect:
            streamer = SystemTelemetryStreamer()
            with self.assertRaises(Exception) as ctx:
                streamer.stream_telemetry(stream_id)

            self.assertEqual(str(ctx.exception), error_message)
            mock_collect.assert_called_once_with(stream_id)

    def test_stream_system_health_telemetry_function(self):
        run_id = uuid.uuid4().hex
        aggregated_health = {
            "run_id": run_id,
            "status": uuid.uuid4().hex,
            "score": random.randint(1, 100)
        }

        result = stream_system_health_telemetry(aggregated_health)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("streamed"))
        self.assertEqual(result.get("processed_run_id"), run_id)
        self.assertIn("timestamp", result)
        self.assertIsInstance(result.get("timestamp"), float)