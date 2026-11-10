import unittest
import uuid
import random
import io
import json
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):

    def test_full_incident_lifecycle_integration(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        anomaly_code = f"ERR_CODE_{random.randint(100, 999)}"
        level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"Integration test anomaly description {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=anomaly_code,
            severity=level,
            description=details,
            metadata={"source": "integration_test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        incident_data = tracker.get_incident(incident_id)
        self.assertIsNotNone(incident_data)
        self.assertEqual(incident_data["id"], incident_id)
        self.assertEqual(incident_data["repo_id"], repo_id)
        self.assertEqual(incident_data["incident_type"], anomaly_code)
        self.assertEqual(incident_data["severity"], level)
        self.assertEqual(incident_data["description"], details)
        self.assertEqual(incident_data["status"], "OPEN")
        
        metrics = tracker.get_incident_metrics(repo_id)
        self.assertEqual(metrics["total"], 1)
        self.assertIn(level, metrics["breakdown"])
        self.assertEqual(metrics["breakdown"][level], 1)
        
        resolver_name = f"dev-{uuid.uuid4()}"
        resolution_note = f"Resolved via test {uuid.uuid4()}"
        resolved = tracker.resolve_incident(incident_id, resolver_name, resolution_note)
        self.assertTrue(resolved)
        
        updated_incident = tracker.get_incident(incident_id)
        self.assertEqual(updated_incident["status"], "RESOLVED")
        self.assertEqual(updated_incident["resolver"], resolver_name)
        self.assertEqual(updated_incident["resolution_notes"], resolution_note)
        
        repos_incidents = tracker.list_incidents_by_repo(repo_id)
        self.assertEqual(len(repos_incidents), 1)
        self.assertEqual(repos_incidents[0]["id"], incident_id)

    def test_ingest_anomaly_stream_integration(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-stream-{uuid.uuid4()}"
        anomaly_code = f"STREAM_ERR_{random.randint(1000, 9999)}"
        level = random.choice(["WARNING", "FATAL"])
        details = f"Stream anomaly details {uuid.uuid4()}"
        
        payload = {
            "repo_id": repo_id,
            "anomaly_code": anomaly_code,
            "level": level,
            "details": details
        }
        
        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
        
        success = tracker.ingest_anomaly_stream(stream)
        self.assertTrue(success)
        
        incidents = tracker.list_incidents_by_repo(repo_id)
        self.assertEqual(len(incidents), 1)
        
        ingested_incident = incidents[0]
        self.assertEqual(ingested_incident["repo_id"], repo_id)
        self.assertEqual(ingested_incident["incident_type"], anomaly_code)
        self.assertEqual(ingested_incident["severity"], level)
        self.assertEqual(ingested_incident["description"], details)
        self.assertEqual(ingested_incident["status"], "OPEN")

    def test_module_level_track_incident(self):
        repo_id = f"repo-func-{uuid.uuid4()}"
        incident_type = f"TYPE_{uuid.uuid4()}"
        severity = "INFO"
        description = f"Desc {uuid.uuid4()}"
        
        incident_id = track_incident(
            repo_id=repo_id,
            incident_type=incident_type,
            severity=severity,
            description=description
        )
        
        self.assertIsNotNone(incident_id)
        uuid.UUID(incident_id)

if __name__ == '__main__':
    unittest.main()