import unittest
import uuid
import random
import os
import tempfile
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster
from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster

class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.exception_msg = f"TestException_{random.randint(100, 999)}"
        self.traceback_str = f"Traceback at line {random.randint(1, 100)}"
        self.channel_name = f"channel_{random.randint(100, 999)}"

        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.temp_dir.name, f"report_{self.incident_id}.txt")

        self.evaluator = IncidentSeverityEvaluator(aggregator=None, template_engine=None)
        self.broadcaster = NotificationWebhookBroadcaster()

        self.broadcaster.register_webhook_channel(
            self.channel_name,
            {"url": "http://localhost:8080/webhook", "method": "POST"}
        )

        self.notification_broadcaster = IncidentNotificationBroadcaster()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_incident_broadcast_chain(self):
        eval_res = self.evaluator.evaluate(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            incident_id=self.incident_id
        )
        severity = eval_res.get("severity") if isinstance(eval_res, dict) else eval_res

        self.assertIn(severity, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        raw_data = {
            "module": self.module_name,
            "error": self.exception_msg,
            "traceback": self.traceback_str,
            "random_salt": random.random()
        }

        result = self.notification_broadcaster.process_and_broadcast(
            incident_id=self.incident_id,
            severity=severity,
            raw_data=raw_data,
            channel_name=self.channel_name
        )

        self.assertIsNotNone(result)

        export_context = {
            "incident_id": self.incident_id,
            "severity": severity,
            "module": self.module_name
        }

        self.broadcaster.export_notification_report(export_context, self.report_path)

        self.assertTrue(os.path.exists(self.report_path), "Файл отчета не был создан в результате цепочки оповещений")

        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.incident_id, content)
            self.assertIn(severity, content)

if __name__ == "__main__":
    unittest.main()