import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.system_health_alert_dispatcher import SystemHealthAlertDispatcher

class TestSystemHealthAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.channel_dispatcher = MagicMock()
        self.template_engine = MagicMock()
        self.webhook_broadcaster = MagicMock()
        self.dispatcher = SystemHealthAlertDispatcher(
            channel_dispatcher=self.channel_dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=self.webhook_broadcaster
        )

    def test_dispatch_critical_alert_success(self):
        alert_id = uuid.uuid4().hex
        severity = random.choice(["CRITICAL", "FATAL", "EMERGENCY"])
        message_body = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        recipient = f"admin_{uuid.uuid4().hex[:6]}@example.com"
        
        expected_template = f"ALERT [{severity}]: {message_body}"
        self.template_engine.render.return_value = expected_template
        self.channel_dispatcher.send.return_value = True

        with patch('skills.system_health_alert_dispatcher.datetime') as mock_dt:
            mock_dt.utcnow.return_value.isoformat.return_value = "2023-10-01T00:00:00"
            
            result = self.dispatcher.dispatch_alert(
                alert_id=alert_id,
                severity=severity,
                payload=message_body,
                recipient=recipient
            )

        self.assertTrue(result)
        self.template_engine.render.assert_called_once_with(
            template_name="critical_alert",
            context={"alert_id": alert_id, "severity": severity, "payload": message_body}
        )
        self.channel_dispatcher.send.assert_called_once_with(
            recipient=recipient,
            content=expected_template
        )

    def test_dispatch_alert_with_webhook_broadcast(self):
        alert_id = uuid.uuid4().hex
        severity = "HIGH"
        payload = uuid.uuid4().hex
        webhook_url = f"https://webhook.example.com/{uuid.uuid4().hex}"
        
        self.template_engine.render.return_value = payload
        self.webhook_broadcaster.broadcast.return_value = {"status": "delivered", "code": 200}

        result = self.dispatcher.dispatch_with_webhook(
            alert_id=alert_id,
            severity=severity,
            payload=payload,
            webhook_url=webhook_url
        )

        self.assertTrue(result.get("success"))
        self.webhook_broadcaster.broadcast.assert_called_once()
        args, kwargs = self.webhook_broadcaster.broadcast.call_args
        self.assertIn(webhook_url, args)
        self.assertIn(alert_id, str(kwargs))

    def test_prioritize_and_dispatch_batch(self):
        alerts = []
        for _ in range(random.randint(3, 7)):
            alerts.append({
                "id": uuid.uuid4().hex,
                "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "message": uuid.uuid4().hex
            })

        sorted_alerts = sorted(alerts, key=lambda x: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}[x["severity"]], reverse=True)
        
        self.channel_dispatcher.batch_send.return_value = len(alerts)

        with patch.object(self.dispatcher, '_sort_alerts_by_severity', return_value=sorted_alerts) as mock_sort:
            dispatched_count = self.dispatcher.dispatch_batch(alerts)

        self.assertEqual(dispatched_count, len(alerts))
        mock_sort.assert_called_once_with(alerts)
        self.channel_dispatcher.batch_send.assert_called_once_with(sorted_alerts)

    def test_alert_stream_processing_from_io(self):
        stream_data = f"ALERT_ID:{uuid.uuid4().hex}|SEV:CRITICAL|MSG:{uuid.uuid4().hex}\n".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        self.template_engine.render.return_value = "rendered_stream_alert"
        self.channel_dispatcher.send.return_value = True

        processed_count = self.dispatcher.process_stream(mock_stream)

        self.assertEqual(processed_count, 1)
        self.channel_dispatcher.send.assert_called()

    def test_dispatch_failure_handling(self):
        alert_id = uuid.uuid4().hex
        severity = "CRITICAL"
        payload = uuid.uuid4().hex
        recipient = uuid.uuid4().hex

        self.template_engine.render.return_value = payload
        self.channel_dispatcher.send.side_effect = ConnectionError("Network unreachable")

        with self.assertRaises(ConnectionError):
            self.dispatcher.dispatch_alert(
                alert_id=alert_id,
                severity=severity,
                payload=payload,
                recipient=recipient
            )

        self.channel_dispatcher.send.assert_called_once()