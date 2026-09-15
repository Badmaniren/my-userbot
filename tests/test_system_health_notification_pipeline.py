import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.system_health_notification_pipeline import SystemHealthNotificationPipeline

class TestSystemHealthNotificationPipeline(unittest.TestCase):

    def setUp(self):
        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.config = {"active": True, "url": f"https://{uuid.uuid4().hex[:8]}.com"}
        self.incident_id = str(random.randint(1000, 9999))
        self.level = random.choice(["CRITICAL", "WARNING", "INFO"])
        self.message = f"msg_{uuid.uuid4().hex[:8]}"

    @patch('skills.system_health_notification_pipeline.SystemHealthAggregator')
    @patch('skills.system_health_notification_pipeline.NotificationChannelDispatcher')
    def test_run_health_check_and_notify_critical(self, mock_dispatcher_cls, mock_aggregator_cls):
        mock_aggregator = mock_aggregator_cls.return_value
        mock_dispatcher = mock_dispatcher_cls.return_value
        
        health_data = {
            "status": "CRITICAL",
            "incident_id": self.incident_id,
            "message": self.message
        }
        mock_aggregator.aggregate_and_report.return_value = health_data
        
        expected_broadcast = {self.channel_name: True}
        mock_dispatcher.broadcast.return_value = expected_broadcast

        pipeline = SystemHealthNotificationPipeline(health_aggregator=mock_aggregator, channel_dispatcher=mock_dispatcher)
        result = pipeline.run_health_check_and_notify()

        mock_aggregator.aggregate_and_report.assert_called_once()
        mock_dispatcher.broadcast.assert_called_once_with(health_data)
        self.assertEqual(result, expected_broadcast)

    @patch('skills.system_health_notification_pipeline.SystemHealthAggregator')
    @patch('skills.system_health_notification_pipeline.NotificationChannelDispatcher')
    def test_run_health_check_and_notify_non_critical(self, mock_dispatcher_cls, mock_aggregator_cls):
        mock_aggregator = mock_aggregator_cls.return_value
        mock_dispatcher = mock_dispatcher_cls.return_value
        
        health_data = {
            "status": random.choice(["OK", "WARNING", "HEALTHY"]),
            "incident_id": self.incident_id,
            "message": self.message
        }
        mock_aggregator.aggregate_and_report.return_value = health_data

        pipeline = SystemHealthNotificationPipeline(health_aggregator=mock_aggregator, channel_dispatcher=mock_dispatcher)
        result = pipeline.run_health_check_and_notify()

        mock_aggregator.aggregate_and_report.assert_called_once()
        mock_dispatcher.broadcast.assert_not_called()
        self.assertEqual(result, {})

    @patch('skills.system_health_notification_pipeline.SystemHealthAggregator')
    @patch('skills.system_health_notification_pipeline.NotificationChannelDispatcher')
    def test_process_stream_and_dispatch(self, mock_dispatcher_cls, mock_aggregator_cls):
        mock_aggregator = mock_aggregator_cls.return_value
        mock_dispatcher = mock_dispatcher_cls.return_value
        
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        path = f"/var/log/{uuid.uuid4().hex[:6]}.log"
        
        parsed_data = {
            "level": self.level,
            "incident_id": self.incident_id,
            "message": self.message
        }
        mock_aggregator.process_stream.return_value = parsed_data
        
        formatted_payload = {"formatted": self.message}
        mock_dispatcher.format_payload.return_value = formatted_payload
        
        expected_broadcast = {self.channel_name: True}
        mock_dispatcher.broadcast.return_value = expected_broadcast

        pipeline = SystemHealthNotificationPipeline(health_aggregator=mock_aggregator, channel_dispatcher=mock_dispatcher)
        result = pipeline.process_stream_and_dispatch(stream_data, path)

        mock_aggregator.process_stream.assert_called_once_with(stream_data, path)
        mock_dispatcher.format_payload.assert_called_once_with(self.level, self.incident_id, self.message)
        mock_dispatcher.broadcast.assert_called_once_with(formatted_payload)
        self.assertEqual(result, expected_broadcast)

    @patch('skills.system_health_notification_pipeline.SystemHealthAggregator')
    @patch('skills.system_health_notification_pipeline.NotificationChannelDispatcher')
    def test_register_alert_channel(self, mock_dispatcher_cls, mock_aggregator_cls):
        mock_dispatcher = mock_dispatcher_cls.return_value
        pipeline = SystemHealthNotificationPipeline(
            health_aggregator=mock_aggregator_cls.return_value,
            channel_dispatcher=mock_dispatcher
        )

        pipeline.register_alert_channel(self.channel_name, self.config)
        mock_dispatcher.register_channel.assert_called_once_with(self.channel_name, self.config)

    @patch('skills.system_health_notification_pipeline.SystemHealthAggregator')
    @patch('skills.system_health_notification_pipeline.NotificationChannelDispatcher')
    def test_send_custom_alert(self, mock_dispatcher_cls, mock_aggregator_cls):
        mock_dispatcher = mock_dispatcher_cls.return_value
        mock_dispatcher.dispatch.return_value = True
        
        payload = {"alert": uuid.uuid4().hex}
        pipeline = SystemHealthNotificationPipeline(
            health_aggregator=mock_aggregator_cls.return_value,
            channel_dispatcher=mock_dispatcher
        )

        result = pipeline.send_custom_alert(self.channel_name, payload)
        mock_dispatcher.dispatch.assert_called_once_with(self.channel_name, payload)
        self.assertTrue(result)

    @patch('skills.system_health_notification_pipeline.SystemHealthAggregator')
    @patch('skills.system_health_notification_pipeline.NotificationChannelDispatcher')
    def test_process_and_notify(self, mock_dispatcher_cls, mock_aggregator_cls):
        mock_aggregator = mock_aggregator_cls.return_value
        mock_dispatcher = mock_dispatcher_cls.return_value
        
        aggregation_mock = {"status": "OK", "id": uuid.uuid4().hex}
        mock_aggregator.aggregate_and_report.return_value = aggregation_mock
        
        mock_dispatcher.channels = {self.channel_name: {"active": False}}
        mock_dispatcher.dispatch.return_value = False
        mock_dispatcher.broadcast.return_value = {self.channel_name: True}

        incidents_list = [{"level": self.level, "id": self.incident_id, "message": self.message}]
        patches_list = [uuid.uuid4().hex]

        pipeline = SystemHealthNotificationPipeline(health_aggregator=mock_aggregator, channel_dispatcher=mock_dispatcher)
        result = pipeline.process_and_notify(incidents_list, patches_list, self.channel_name)

        mock_aggregator.aggregate_and_report.assert_called_once()
        self.assertTrue(mock_dispatcher.channels[self.channel_name]["active"])
        mock_dispatcher.dispatch.assert_called_once()
        mock_dispatcher.broadcast.assert_called_once()
        
        self.assertIn("aggregation_result", result)
        self.assertIn("dispatch_result", result)
        self.assertEqual(result["aggregation_result"], aggregation_mock)
        self.assertTrue(result["dispatch_result"])

if __name__ == '__main__':
    unittest.main()