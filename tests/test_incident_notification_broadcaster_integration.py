import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.test_dir)

        self.dispatcher = NotificationChannelDispatcher()
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=None,
            webhook_broadcaster=None,
            storage_dir=self.storage_path,
            severity_evaluator=None
        )
        self.broadcaster = IncidentNotificationBroadcaster(
            bridge=self.bridge,
            dispatcher=self.dispatcher
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_mass_broadcast_and_persistence_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        channel_name_1 = f"syslog_{random_suffix}"
        channel_name_2 = f"webhook_{random_suffix}"

        config_1 = {"target": f"/var/log/incident_{random_suffix}.log"}
        config_2 = {"url": f"http://localhost:8080/hook/{random_suffix}"}

        self.dispatcher.register_channel(channel_name_1, config_1)
        self.dispatcher.register_channel(channel_name_2, config_2)

        incident_id = str(uuid.uuid4())
        severity_levels = ["INFO", "WARNING", "CRITICAL", "EMERGENCY"]
        chosen_severity = random.choice(severity_levels)
        random_error_code = random.randint(1000, 9999)
        incident_message = f"Integration test failure code {random_error_code}"

        incident_data = {
            "id": incident_id,
            "level": chosen_severity,
            "message": incident_message
        }

        result = self.broadcaster.broadcast_alert(incident_data)

        self.assertIsInstance(result, dict)
        self.assertIn(channel_name_1, result)
        self.assertIn(channel_name_2, result)
        self.assertTrue(result[channel_name_1])
        self.assertTrue(result[channel_name_2])

        expected_file = self.storage_path / f"incident_{incident_id}.json"
        self.assertTrue(expected_file.exists(), "Модуль должен сохранять информацию об инциденте на диск")

        file_content = expected_file.read_text(encoding="utf-8")
        self.assertIn(incident_id, file_content)
        self.assertIn(incident_message, file_content)


if __name__ == "__main__":
    unittest.main()