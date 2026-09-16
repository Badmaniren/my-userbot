import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster

class TestIncidentNotificationBroadcaster(unittest.TestCase):
    def setUp(self):
        self.dispatcher = MagicMock()
        self.template_engine = MagicMock()
        self.webhook_broadcaster = MagicMock()
        self.storage_dir = uuid.uuid4().hex

        self.broadcaster = IncidentNotificationBroadcaster(
            dispatcher=self.dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=self.webhook_broadcaster,
            storage_dir=self.storage_dir
        )

    def test_broadcast_incident_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        incident_data = {rand_key: rand_val}
        channel = uuid.uuid4().hex
        template = uuid.uuid4().hex
        expected_severity = uuid.uuid4().hex
        expected_bridge_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.broadcaster.evaluator, 'calculate_severity_score', return_value=expected_severity) as mock_eval, \
             patch.object(self.broadcaster.bridge, 'process_incident', return_value=expected_bridge_result) as mock_bridge:

            res = self.broadcaster.broadcast_incident(incident_data, channel, template)

            mock_eval.assert_called_once_with(incident_data)
            mock_bridge.assert_called_once_with(incident_data, channel, template, expected_severity)
            self.assertEqual(res["severity"], expected_severity)
            self.assertEqual(res[list(expected_bridge_result.keys())[0]], list(expected_bridge_result.values())[0])

    def test_ingest_and_broadcast_stream(self):
        stream_content = uuid.uuid4().bytes
        file_stream = io.BytesIO(stream_content)
        channel = uuid.uuid4().hex
        expected_return = uuid.uuid4().hex

        with patch.object(self.broadcaster.bridge, 'ingest_stream', return_value=expected_return) as mock_ingest:
            res = self.broadcaster.ingest_and_broadcast_stream(file_stream, channel)
            mock_ingest.assert_called_once_with(file_stream, channel)
            self.assertEqual(res, expected_return)

    def test_dispatch_critical_broadcast(self):
        aggregated_incident = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_return = uuid.uuid4().hex

        with patch.object(self.broadcaster.bridge, 'dispatch_critical_incident', return_value=expected_return) as mock_dispatch:
            res = self.broadcaster.dispatch_critical_broadcast(aggregated_incident)
            mock_dispatch.assert_called_once_with(aggregated_incident)
            self.assertEqual(res, expected_return)

    def test_process_and_broadcast_with_bridge_method(self):
        incident_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        channel = uuid.uuid4().hex
        template = uuid.uuid4().hex
        expected_return = uuid.uuid4().hex

        self.broadcaster.bridge.process_and_broadcast = MagicMock(return_value=expected_return)

        res = self.broadcaster.process_and_broadcast(incident_data, channel, template)
        self.broadcaster.bridge.process_and_broadcast.assert_called_once_with(incident_data, channel, template)
        self.assertEqual(res, expected_return)

    def test_process_and_broadcast_fallback(self):
        incident_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        channel = uuid.uuid4().hex
        template = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        expected_return = uuid.uuid4().hex

        if hasattr(self.broadcaster.bridge, "process_and_broadcast"):
            delattr(self.broadcaster.bridge, "process_and_broadcast")

        with patch.object(self.broadcaster.evaluator, 'calculate_severity_score', return_value=severity) as mock_eval, \
             patch.object(self.broadcaster.bridge, 'process_incident', return_value=expected_return) as mock_bridge:

            res = self.broadcaster.process_and_broadcast(incident_data, channel, template)

            mock_eval.assert_called_once_with(incident_data)
            mock_bridge.assert_called_once_with(incident_data, channel, template, severity)
            self.assertEqual(res, expected_return)

if __name__ == '__main__':
    unittest.main()