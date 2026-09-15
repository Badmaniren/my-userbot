import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.incident_notification_broadcaster import (
    IncidentNotificationBroadcaster,
    broadcast_incident_pipeline
)

class TestIncidentNotificationBroadcaster(unittest.TestCase):

    def setUp(self):
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Exc_{uuid.uuid4().hex[:8]}"
        self.traceback_str = f"Traceback_{uuid.uuid4().hex[:8]}"
        self.incident_id = f"INC-{random.randint(1000, 9999)}"
        self.webhook_url = f"https://webhook.example.com/{uuid.uuid4().hex[:6]}"
        self.channel = f"channel_{uuid.uuid4().hex[:6]}"
        self.template = f"template_{uuid.uuid4().hex[:6]}"

    def test_broadcaster_init_defaults(self):
        broadcaster = IncidentNotificationBroadcaster()
        self.assertIsNotNone(broadcaster.evaluator)
        self.assertIsNotNone(broadcaster.bridge)

    def test_broadcaster_init_injected(self):
        mock_evaluator = MagicMock()
        mock_bridge = MagicMock()
        broadcaster = IncidentNotificationBroadcaster(
            severity_evaluator=mock_evaluator,
            notification_bridge=mock_bridge
        )
        self.assertEqual(broadcaster.evaluator, mock_evaluator)
        self.assertEqual(broadcaster.bridge, mock_bridge)

    def test_process_and_broadcast_success(self):
        mock_evaluator = MagicMock()
        mock_bridge = MagicMock()

        evaluated_data = {
            'incident_id': self.incident_id,
            'severity_score': 'HIGH'
        }
        mock_evaluator.evaluate.return_value = evaluated_data

        broadcaster = IncidentNotificationBroadcaster(
            severity_evaluator=mock_evaluator,
            notification_bridge=mock_bridge
        )

        result = broadcaster.process_and_broadcast(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            incident_id=self.incident_id,
            webhook_url=self.webhook_url,
            channel=self.channel,
            template=self.template
        )

        mock_evaluator.evaluate.assert_called_once()
        mock_bridge.process_incident.assert_called_once_with(
            evaluated_data,
            self.channel,
            self.template,
            webhook_url=self.webhook_url
        )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['incident_id'], self.incident_id)
        self.assertEqual(result['severity'], 'HIGH')

    def test_process_and_broadcast_exception_handling(self):
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.side_effect = RuntimeError("Evaluation failed")

        broadcaster = IncidentNotificationBroadcaster(severity_evaluator=mock_evaluator)

        result = broadcaster.process_and_broadcast(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str
        )

        self.assertEqual(result['status'], 'error')
        self.assertIn("Evaluation failed", result['error_message'])

    def test_ingest_and_broadcast_stream(self):
        mock_evaluator = MagicMock()
        mock_bridge = MagicMock()

        aggregated_data = {'summary': uuid.uuid4().hex}
        mock_evaluator.evaluate_stream.return_value = aggregated_data

        stream_data = io.BytesIO(uuid.uuid4().bytes)

        broadcaster = IncidentNotificationBroadcaster(
            severity_evaluator=mock_evaluator,
            notification_bridge=mock_bridge
        )

        result = broadcaster.ingest_and_broadcast_stream(
            module_name=self.module_name,
            file_stream=stream_data,
            channel=self.channel,
            webhook_url=self.webhook_url
        )

        mock_evaluator.evaluate_stream.assert_called_once_with(self.module_name, stream_data)
        mock_bridge.ingest_stream.assert_called_once_with(self.module_name, stream_data)
        mock_bridge.dispatch_critical_incident.assert_called_once_with(aggregated_data)

        self.assertEqual(result['module'], self.module_name)
        self.assertEqual(result['broadcast_target'], self.webhook_url)

    def test_broadcast_incident_pipeline_standalone(self):
        evaluated_data = {
            'incident_id': self.incident_id,
            'severity_score': 'CRITICAL'
        }

        with patch('skills.incident_notification_broadcaster.IncidentSeverityEvaluator') as mock_eval_cls, \
             patch('skills.incident_notification_broadcaster.IncidentNotificationBridge') as mock_bridge_cls:

            mock_eval_instance = mock_eval_cls.return_value
            mock_eval_instance.evaluate.return_value = evaluated_data
            mock_bridge_instance = mock_bridge_cls.return_value

            res = broadcast_incident_pipeline(
                module_name=self.module_name,
                exception=Exception(self.exception_msg),
                traceback_str=self.traceback_str,
                incident_id=self.incident_id,
                channel=self.channel,
                template=self.template
            )

            mock_eval_instance.evaluate.assert_called_once()
            mock_bridge_instance.process_incident.assert_called_once_with(
                evaluated_data,
                self.channel,
                self.template
            )
            self.assertEqual(res, evaluated_data)