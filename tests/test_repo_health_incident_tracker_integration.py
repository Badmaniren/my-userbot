import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/test_repo_{uuid.uuid4().hex}"
        self.tracker = RepoHealthIncidentTracker(repo_path=self.repo_path)
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        self.message = f"Test incident message {uuid.uuid4().hex}"

    def test_log_incident_integration(self):
        try:
            self.tracker.log_incident(self.incident_id, self.severity, self.message)
        except Exception as e:
            self.fail(f"log_incident raised an exception unexpectedly: {e}")

    def test_register_and_get_incident_integration(self):
        details = {"error_code": random.randint(1000, 9999), "context": uuid.uuid4().hex}
        registered = self.tracker.register_incident(self.incident_id, details)

        self.assertIsInstance(registered, dict)
        self.assertEqual(registered["incident_id"], self.incident_id)
        self.assertEqual(registered["details"], details)
        self.assertEqual(registered["status"], "RESOLVED")

        fetched = self.tracker.get_incident(self.incident_id)
        self.assertIsInstance(fetched, dict)
        self.assertEqual(fetched["incident_id"], self.incident_id)
        self.assertEqual(fetched["status"], "RESOLVED")

    def test_process_incident_stream_integration(self):
        stream_data = f"STREAM_DATA_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(stream_data)
        try:
            result = self.tracker.process_incident_stream(stream)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"process_incident_stream failed with real stream: {e}")

    def test_check_anomaly_status_integration(self):
        incident_code = f"INC-{random.randint(100, 999)}"
        try:
            result = self.tracker.check_anomaly_status(incident_code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"check_anomaly_status raised an exception: {e}")

    def test_dispatch_incident_integration(self):
        incident_type = random.choice(["SECURITY", "PERFORMANCE", "DEPENDENCY"])
        payload = {"payload_id": uuid.uuid4().hex, "value": random.random()}
        try:
            result = self.tracker.dispatch_incident(incident_type, payload)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"dispatch_incident raised an exception: {e}")

    def test_verify_repo_health_integration(self):
        token = uuid.uuid4().hex
        try:
            result = self.tracker.verify_repo_health(self.repo_path, token)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"verify_repo_health raised an exception: {e}")

    def test_trigger_remediation_integration(self):
        anomaly_id = f"ANOMALY-{uuid.uuid4().hex[:8]}"
        target_repo = f"https://github.com/test-org/repo-{uuid.uuid4().hex[:6]}.git"
        try:
            result = self.tracker.trigger_remediation(anomaly_id, target_repo)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"trigger_remediation raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()