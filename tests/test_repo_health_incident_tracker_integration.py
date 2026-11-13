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
        self.anomaly_code = f"ERR_CODE_{random.randint(1000, 9999)}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = f"Test anomaly description {uuid.uuid4()}"

    def test_full_incident_lifecycle_and_metrics(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.anomaly_code,
            severity=self.severity,
            description=self.description,
            metadata={"source": "integration_test", "run_id": random.randint(1, 100)}
        )
        
        self.assertIsNotNone(incident_id)
        
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.anomaly_code)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["status"], "OPEN")

        metrics = self.tracker.get_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 1)
        self.assertEqual(metrics["breakdown"].get(self.severity), 1)

        resolver_name = f"admin-{uuid.uuid4()}"
        resolution_notes = f"Fixed via test run {uuid.uuid4()}"
        resolved = self.tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolved)

        updated_incident = self.tracker.get_incident(incident_id)
        self.assertEqual(updated_incident["status"], "RESOLVED")
        self.assertEqual(updated_incident["resolver"], resolver_name)
        self.assertEqual(updated_incident["resolution_notes"], resolution_notes)

    def test_ingest_anomaly_stream_integration(self):
        stream_payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.anomaly_code,
            "level": self.severity,
            "details": self.description
        }
        stream_bytes = json.dumps(stream_payload).encode("utf-8")
        stream_mock = io.BytesIO(stream_bytes)

        ingested = self.tracker.ingest_anomaly_stream(stream_mock)
        self.assertTrue(ingested)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.anomaly_code)
        self.assertEqual(incidents[0]["severity"], self.severity)

    def test_global_track_incident_wrapper(self):
        global_incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.anomaly_code,
            severity=self.severity,
            description=self.description
        )
        self.assertIsNotNone(global_incident_id)

if __name__ == "__main__":
    unittest.main()