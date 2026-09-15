import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster

class TestIncidentNotificationBroadcaster(unittest.TestCase):

    def setUp(self):
        self.aggregator_mock = MagicMock()
        self.template_engine_mock = MagicMock()

        self.evaluator = IncidentSeverityEvaluator(
            aggregator=self.aggregator_mock,
            template_engine=self.template_engine_mock
        )
        self.broadcaster = NotificationWebhookBroadcaster()

        self.incident_broadcaster = IncidentNotificationBroadcaster(
            severity_evaluator=self.evaluator,
            webhook_broadcaster=self.broadcaster
        )

    def test_composition_and_initialization(self):
        rand_str_1 = uuid.uuid4().hex
        rand_str_2 = uuid.uuid4().hex

        evaluator_mock = MagicMock(spec=IncidentSeverityEvaluator)
        broadcaster_mock = MagicMock(spec=NotificationWebhookBroadcaster)

        composite = IncidentNotificationBroadcaster(
            severity_evaluator=evaluator_mock,
            webhook_broadcaster=broadcaster_mock
        )

        self.assertEqual(composite.severity_evaluator, evaluator_mock)
        self.assertEqual(composite.webhook_broadcaster, broadcaster_mock)

    def test_evaluate_and_broadcast_success(self):
        module_name = "".join(random.choices(string.ascii_lowercase, k=10))
        exception_msg = "".join(random.choices(string.ascii_letters, k=15))
        exc_type = type(exception_msg, (Exception,), {})
        exception_instance = exc_type(exception_msg)
        tb_str = "".join(random.choices(string.printable, k=30))
        incident_id = uuid.uuid4().hex
        expected_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        template_name = "".join(random.choices(string.ascii_lowercase, k=8))

        with patch.object(self.evaluator, 'evaluate', return_value=expected_severity) as mock_evaluate, \
             patch.object(self.broadcaster, 'broadcast_incident') as mock_broadcast:

            raw_data = {
                "module": module_name,
                "error": exception_msg,
                "traceback": tb_str,
                "id": incident_id
            }

            result = self.incident_broadcaster.handle_and_broadcast(
                module_name=module_name,
                exception=exception_instance,
                traceback_str=tb_str,
                incident_id=incident_id,
                template_name=template_name,
                raw_data=raw_data
            )

            mock_evaluate.assert_called_once_with(module_name, exception_instance, tb_str, incident_id)
            mock_broadcast.assert_called_once_with(
                severity=expected_severity,
                incident_id=incident_id,
                raw_data=raw_data,
                template_name=template_name
            )
            self.assertEqual(result, expected_severity)

    def test_stream_processing_and_broadcasting(self):
        stream_size = random.randint(5, 15)
        stream_data = [
            {
                "id": uuid.uuid4().hex,
                "module": "".join(random.choices(string.ascii_lowercase, k=6)),
                "message": uuid.uuid4().hex
            }
            for _ in range(stream_size)
        ]
        assigned_severity = random.choice(["INFO", "WARNING", "FATAL"])

        with patch.object(self.evaluator, 'evaluate_stream') as mock_eval_stream, \
             patch.object(self.broadcaster, 'process_stream_and_broadcast') as mock_proc_stream:

            mock_eval_stream.return_value = assigned_severity

            module_name = "".join(random.choices(string.ascii_lowercase, k=8))
            self.incident_broadcaster.process_stream_chain(module_name, stream_data, assigned_severity)

            mock_eval_stream.assert_called_once_with(module_name, stream_data)
            mock_proc_stream.assert_called_once_with(stream_data, assigned_severity)

    def test_broadcast_with_custom_channels(self):
        channel_name = "".join(random.choices(string.ascii_lowercase, k=7))
        config = {"url": f"https://{uuid.uuid4().hex}.com/webhook"}
        severity = random.choice(["DEBUG", "ERROR"])
        incident_id = uuid.uuid4().hex
        payload = {"data": uuid.uuid4().hex}

        with patch.object(self.broadcaster, 'register_webhook_channel') as mock_register, \
             patch.object(self.broadcaster, 'dispatch_to_webhook') as mock_dispatch:

            self.incident_broadcaster.register_and_dispatch(channel_name, config, channel_name, payload)

            mock_register.assert_called_once_with(channel_name, config)
            mock_dispatch.assert_called_once_with(channel_name, payload)

    def test_export_pipeline_report(self):
        context = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        file_path = f"/tmp/{uuid.uuid4().hex}.json"

        with patch.object(self.broadcaster, 'export_notification_report') as mock_export:
            self.incident_broadcaster.export_report(context, file_path)
            mock_export.assert_called_once_with(context, file_path)

    def test_stream_bytes_input_handling(self):
        random_bytes = b"".join(bytes(random.getrandbits(8)) for _ in range(64))
        stream_io = io.BytesIO(random_bytes)

        module_name = "".join(random.choices(string.ascii_lowercase, k=5))
        severity = random.choice(["LOW", "HIGH"])

        with patch.object(self.evaluator, 'evaluate_stream') as mock_eval, \
             patch.object(self.broadcaster, 'process_stream_and_broadcast') as mock_broadcast:

            self.incident_broadcaster.handle_stream_bytes(module_name, stream_io, severity)

            mock_eval.assert_called_once()
            mock_broadcast.assert_called_once()

    def test_exception_propagation_on_evaluation_failure(self):
        module_name = uuid.uuid4().hex
        exc = RuntimeError(uuid.uuid4().hex)
        tb = uuid.uuid4().hex
        inc_id = uuid.uuid4().hex

        with patch.object(self.evaluator, 'evaluate', side_effect=ValueError(uuid.uuid4().hex)) as mock_eval, \
             patch.object(self.broadcaster, 'broadcast_incident') as mock_broadcast:

            with self.assertRaises(ValueError):
                self.incident_broadcaster.handle_and_broadcast(module_name, exc, tb, inc_id)

            mock_broadcast.assert_not_called()

    def test_uuid_and_randomness_integrity(self):
        unique_id = uuid.uuid4().hex
        module_name = f"mod_{uuid.uuid4().hex}"
        exc = Exception(uuid.uuid4().hex)
        tb = uuid.uuid4().hex
        severity = uuid.uuid4().hex

        with patch.object(self.evaluator, 'evaluate', return_value=severity) as mock_eval, \
             patch.object(self.broadcaster, 'broadcast_incident', return_value=True) as mock_broadcast:

            res = self.incident_broadcaster.handle_and_broadcast(module_name, exc, tb, unique_id)

            self.assertEqual(res, severity)
            _, kwargs = mock_broadcast.call_args
            self.assertEqual(kwargs['incident_id'], unique_id)
            self.assertEqual(kwargs['severity'], severity)

if __name__ == '__main__':
    unittest.main()