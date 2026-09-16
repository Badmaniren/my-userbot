import unittest
import uuid
import random
import tempfile
import os
from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster

class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_dir = tempfile.TemporaryDirectory()
        self.broadcaster = IncidentNotificationBroadcaster(
            dispatcher=None,
            template_engine=None,
            webhook_broadcaster=None,
            storage_dir=self.storage_dir.name
        )

    def tearDown(self):
        self.storage_dir.cleanup()

    def test_broadcast_incident_real_integration(self):
        random_id = str(uuid.uuid4())
        random_score_factor = random.randint(10, 100)

        incident_data = {
            "incident_id": random_id,
            "module_name": f"test_module_{random_id[:8]}",
            "exception": f"RuntimeError: simulated failure {random_score_factor}",
            "traceback": "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise RuntimeError()",
            "metrics": {"error_count": random_score_factor}
        }

        channel = f"channel_{random.randint(100, 999)}"
        template = "default_incident_template"

        result = self.broadcaster.broadcast_incident(incident_data, channel, template)

        self.assertIsInstance(result, dict)
        self.assertIn("severity", result)
        self.assertTrue(len(result["severity"]) > 0)

    def test_ingest_and_broadcast_stream_integration(self):
        stream_id = str(uuid.uuid4())
        stream_content = f"INCIDENT_STREAM_DATA_{stream_id}\nCRITICAL: Database connection lost."

        file_stream = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        file_stream.write(stream_content)
        file_stream.seek(0)
        file_path = file_stream.name
        file_stream.close()

        try:
            with open(file_path, 'r') as f:
                channel = f"stream_channel_{random.randint(1, 100)}"
                result = self.broadcaster.ingest_and_broadcast_stream(f, channel)
                self.assertIsNotNone(result)
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == "__main__":
    unittest.main()