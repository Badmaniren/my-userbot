import unittest
import uuid
import random
import io
import json
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_anomaly_code = f"ERR-{random.randint(1000, 9999)}"
        self.random_description = f"Random test incident description {uuid.uuid4()}"

    def test_incident_lifecycle_and_metrics_integration(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.random_anomaly_code,
            severity=self.random_severity,
            description=self.random_description,
            metadata={"env": "integration-test", "random_val": random.random()}
        )
        
        self.assertIsNotNone(incident_id)
        
        retrieved_incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(retrieved_incident)
        self.assertEqual(retrieved_incident["id"], incident_id)
        self.assertEqual(retrieved_incident["repo_id"], self.repo_id)
        self.assertEqual(retrieved_incident["incident_type"], self.random_anomaly_code)
        self.assertEqual(retrieved_incident["severity"], self.random_severity)
        self.assertEqual(retrieved_incident["description"], self.random_description)
        self.assertEqual(retrieved_incident["status"], "OPEN")

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 1)
        self.assertIn(self.random_severity, metrics["breakdown"])
        self.assertEqual(metrics["breakdown"][self.random_severity], 1)

        resolver_name = f"user-{uuid.uuid4()}"
        resolution_text = f"Resolved via integration test {uuid.uuid4()}"
        resolved = self.tracker.resolve_incident(incident_id, resolver=resolver_name, resolution_notes=resolution_text)
        self.assertTrue(resolved)

        updated_incident = self.tracker.get_incident(incident_id)
        self.assertEqual(updated_incident["status"], "RESOLVED")
        self.assertEqual(updated_incident["resolver"], resolver_name)
        self.assertEqual(updated_incident["resolution_notes"], resolution_text)

    def test_ingest_anomaly_stream_integration(self):
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.random_anomaly_code,
            "level": self.random_severity,
            "details": self.random_description
        }
        stream_data = json.dumps(payload).encode("utf-8")
        stream = io.BytesIO(stream_data)

        success = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(success)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.random_anomaly_code)
        self.assertEqual(incidents[0]["severity"], self.random_severity)
        self.assertEqual(incidents[0]["description"], self.random_description)

    def test_global_track_incident_wrapper(self):
        global_incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.random_anomaly_code,
            severity=self.random_severity,
            description=self.random_description
        )
        self.assertIsNotNone(global_incident_id)
        self.assertIsInstance(global_incident_id, str)

if __name__ == "__main__":
    unittest.main()