import unittest
import uuid
import random
import io
from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster, broadcast_incident_pipeline

class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):
    def setUp(self):
        self.broadcaster = IncidentNotificationBroadcaster()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"Critical failure in subsystem {random.randint(1000, 9999)}"
        self.random_traceback = f"Traceback (most recent call last):\n  File '{self.random_module_name}.py', line {random.randint(1, 100)}\nException: {self.random_error_msg}"
        self.random_webhook = f"https://webhook.site/{uuid.uuid4()}"

    def test_process_and_broadcast_integration(self):
        try:
            exception_obj = RuntimeError(self.random_error_msg)
            result = self.broadcaster.process_and_broadcast(
                module_name=self.random_module_name,
                exception=exception_obj,
                traceback_str=self.random_traceback,
                incident_id=self.random_incident_id,
                webhook_url=self.random_webhook,
                channel="console",
                template=None
            )

            self.assertIsInstance(result, dict)
            self.assertIn('status', result)
            self.assertEqual(result.get('incident_id'), self.random_incident_id)
            self.assertIn('severity', result)
        except Exception as e:
            self.fail(f"Integration test failed with real components: {e}")

    def test_ingest_and_broadcast_stream_integration(self):
        try:
            stream_data = f"LOG STREAM DATA {uuid.uuid4()}\nERROR: {self.random_error_msg}"
            file_stream = io.StringIO(stream_data)

            result = self.broadcaster.ingest_and_broadcast_stream(
                module_name=self.random_module_name,
                file_stream=file_stream,
                channel="console",
                webhook_url=self.random_webhook
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('module'), self.random_module_name)
            self.assertEqual(result.get('broadcast_target'), self.random_webhook)
        except Exception as e:
            self.fail(f"Stream integration test failed with real components: {e}")

    def test_broadcast_incident_pipeline_integration(self):
        try:
            exception_obj = ValueError(self.random_error_msg)
            evaluated = broadcast_incident_pipeline(
                module_name=self.random_module_name,
                exception=exception_obj,
                traceback_str=self.random_traceback,
                incident_id=self.random_incident_id,
                channel="console",
                template=None
            )

            self.assertIsInstance(evaluated, dict)
            self.assertIn('incident_id', evaluated)
            self.assertEqual(evaluated.get('incident_id'), self.random_incident_id)
            self.assertIn('severity_score', evaluated)
        except Exception as e:
            self.fail(f"Pipeline integration test failed with real components: {e}")

if __name__ == '__main__':
    unittest.main()