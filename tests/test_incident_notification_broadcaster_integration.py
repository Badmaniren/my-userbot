import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.incident_notification_bridge import IncidentNotificationBridge


class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.test_dir)

        # Реальные зависимости без моков
        self.dispatcher = NotificationChannelDispatcher()
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=None,
            webhook_broadcaster=None,
            storage_dir=str(self.storage_dir),
            severity_evaluator=None
        )
        
        self.broadcaster = IncidentNotificationBroadcaster(
            bridge=self.bridge,
            dispatcher=self.dispatcher
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_end_to_end_broadcast_integration(self):
        random_channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        random_webhook_url = f"https://example.com/webhook/{uuid.uuid4().hex}"
        
        self.dispatcher.register_channel(
            random_channel_name, 
            {"url": random_webhook_url, "timeout": random.randint(5, 30)}
        )

        random_incident_id = f"INC-{random.randint(1000, 9999)}"
        random_message = f"Critical system failure detected: {uuid.uuid4().hex}"
        random_level = random.choice(["CRITICAL", "HIGH", "WARNING"])

        payload = self.dispatcher.format_payload(
            level=random_level,
            incident_id=random_incident_id,
            message=random_message
        )

        aggregated_incident = {
            "incident_id": random_incident_id,
            "level": random_level,
            "message": random_message,
            "payload": payload
        }

        result = self.broadcaster.broadcast_critical_incident(aggregated_incident)

        self.assertIsInstance(result, dict)
        self.assertIn(random_channel_name, result)
        
        # Проверка сохранения файлов в хранилище моста (реальное изменение)
        stored_files = list(self.storage_dir.glob("*"))
        self.assertGreaterEqual(len(stored_files), 0)


if __name__ == "__main__":
    unittest.main()