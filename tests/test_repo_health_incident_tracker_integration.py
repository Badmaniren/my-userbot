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
        self.incident_type = f"ANOMALY_CODE_{random.randint(1000, 9999)}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = f"Random integration test anomaly description {uuid.uuid4()}"

    def test_full_incident_lifecycle_and_remediation_pipeline(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata={"source": "integration_test", "random_val": random.random()}
        )
        
        self.assertIsNotNone(incident_id)
        
        retrieved = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], incident_id)
        self.assertEqual(retrieved["repo_id"], self.repo_id)
        self.assertEqual(retrieved["incident_type"], self.incident_type)
        self.assertEqual(retrieved["severity"], self.severity)
        self.assertEqual(retrieved["status"], "OPEN")
        
        metrics_before = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics_before["total"], 1)
        self.assertIn(self.severity, metrics_before["breakdown"])
        self.assertEqual(metrics_before["breakdown"][self.severity], 1)
        
        resolver_name = f"auto-remediator-{uuid.uuid4()}"
        resolution_notes = f"Successfully remediated via pipeline sync {uuid.uuid4()}"
        resolved = self.tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolved)
        
        retrieved_resolved = self.tracker.get_incident(incident_id)
        self.assertEqual(retrieved_resolved["status"], "RESOLVED")
        self.assertEqual(retrieved_resolved["resolver"], resolver_name)
        self.assertEqual(retrieved_resolved["resolution_notes"], resolution_notes)

    def test_anomaly_stream_ingestion_integration(self):
        stream_payload = {
            "repo_id": self.repo_id,
            "anomaly_code": f"STREAM_ERR_{random.randint(100, 999)}",
            "level": random.choice(["WARNING", "ERROR"]),
            "details": f"Stream anomaly details {uuid.uuid4()}"
        }
        stream_bytes = json.dumps(stream_payload).encode("utf-8")
        stream_obj = io.BytesIO(stream_bytes)
        
        success = self.tracker.ingest_anomaly_stream(stream_obj)
        self.assertTrue(success)
        
        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], stream_payload["anomaly_code"])
        self.assertEqual(incidents[0]["description"], stream_payload["details"])

    def test_global_track_incident_helper(self):
        global_incident_type = f"GLOBAL_{random.randint(10000, 99999)}"
        global_incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=global_incident_type,
            severity="HIGH",
            description="Testing global helper function"
        )
        self.assertIsNotNone(global_incident_id)

if __name__ == "__main__":
    unittest.main()