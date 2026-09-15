import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.system_health_notification_pipeline import SystemHealthNotificationPipeline
from skills.system_health_aggregator import SystemHealthAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestSystemHealthNotificationPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = SystemHealthNotificationPipeline()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_incident_id = uuid.uuid4().hex
        self.random_message = ''.join(random.choices(string.ascii_letters, k=20))
        self.random_level = random.choice(['CRITICAL', 'ERROR', 'WARNING', 'FATAL'])
        self.random_channel = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_config = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_pipeline_initialization(self):
        self.assertIsInstance(self.pipeline.aggregator, SystemHealthAggregator)
        self.assertIsInstance(self.pipeline.dispatcher, NotificationChannelDispatcher)

    def test_run_health_check_and_notify_success(self):
        mock_health_data = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": "CRITICAL",
            "incident_id": self.random_incident_id,
            "message": self.random_message
        }

        with patch.object(SystemHealthAggregator, 'aggregate_and_report', return_value=mock_health_data) as mock_aggregate, \
             patch.object(NotificationChannelDispatcher, 'broadcast', return_value={self.random_channel: True}) as mock_broadcast:

            result = self.pipeline.run_health_check_and_notify()

            mock_aggregate.assert_called_once()
            mock_broadcast.assert_called_once()
            self.assertIn(self.random_channel, result)
            self.assertTrue(result[self.random_channel])

    def test_run_health_check_and_notify_no_critical(self):
        mock_health_data = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": "HEALTHY"
        }

        with patch.object(SystemHealthAggregator, 'aggregate_and_report', return_value=mock_health_data) as mock_aggregate, \
             patch.object(NotificationChannelDispatcher, 'broadcast') as mock_broadcast:

            result = self.pipeline.run_health_check_and_notify()

            mock_aggregate.assert_called_once()
            mock_broadcast.assert_not_called()
            self.assertEqual(result, {})

    def test_process_stream_and_dispatch(self):
        random_stream_content = json_bytes = io.BytesIO(f'{{"incident_id": "{self.random_incident_id}", "level": "{self.random_level}", "message": "{self.random_message}"}}'.encode('utf-8'))
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        parsed_data = {
            "incident_id": self.random_incident_id,
            "level": self.random_level,
            "message": self.random_message
        }

        formatted_payload = {
            "id": self.random_incident_id,
            "lvl": self.random_level,
            "msg": self.random_message
        }

        with patch.object(SystemHealthAggregator, 'process_stream', return_value=parsed_data) as mock_process, \
             patch.object(NotificationChannelDispatcher, 'format_payload', return_value=formatted_payload) as mock_format, \
             patch.object(NotificationChannelDispatcher, 'broadcast', return_value={self.random_channel: True}) as mock_broadcast:

            result = self.pipeline.process_stream_and_dispatch(random_stream_content, random_path)

            mock_process.assert_called_once_with(random_stream_content, random_path)
            mock_format.assert_called_once_with(self.random_level, self.random_incident_id, self.random_message)
            mock_broadcast.assert_called_once_with(formatted_payload)
            self.assertTrue(result.get(self.random_channel))

    def test_register_and_dispatch_custom_alert(self):
        with patch.object(NotificationChannelDispatcher, 'register_channel') as mock_register, \
             patch.object(NotificationChannelDispatcher, 'dispatch', return_value=True) as mock_dispatch:

            self.pipeline.register_alert_channel(self.random_channel, self.random_config)
            mock_register.assert_called_once_with(self.random_channel, self.random_config)

            payload = {
                uuid.uuid4().hex: self.random_message
            }
            dispatch_result = self.pipeline.send_custom_alert(self.random_channel, payload)

            mock_dispatch.assert_called_once_with(self.random_channel, payload)
            self.assertTrue(dispatch_result)


if __name__ == '__main__':
    unittest.main()