import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_incident_lifecycle_and_dispatch_aggregation(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        anomaly_codes = ["HIGH_CPU_LOAD", "MEMORY_LEAK", "DISK_FULL", "DEADLOCK"]
        severities = ["CRITICAL", "WARNING", "INFO"]
        
        selected_code = random.choice(anomaly_codes)
        selected_severity = random.choice(severities)
        description = f"Auto-generated integration test incident {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=selected_code,
            severity=selected_severity,
            description=description,
            metadata={"source": "integration_test", "random_seed": random.randint(1, 1000)}
        )
        
        self.assertIsNotNone(incident_id)
        
        retrieved = tracker.get_incident(incident_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], incident_id)
        self.assertEqual(retrieved["repo_id"], repo_id)
        self.assertEqual(retrieved["incident_type"], selected_code)
        self.assertEqual(retrieved["severity"], selected_severity)
        self.assertEqual(retrieved["description"], description)
        self.assertEqual(retrieved["status"], "OPEN")
        
        payload_data = {
            "repo_id": repo_id,
            "anomaly_code": random.choice(anomaly_codes),
            "level": random.choice(severities),
            "details": f"Stream anomaly {uuid.uuid4()}"
        }
        stream_mock = io.BytesIO(str(uuid.uuid4()).encode("utf-8"))
        stream_mock.read = lambda: str(payload_data).replace("'", '"').encode("utf-8")
        
        ingest_result = tracker.ingest_anomaly_stream(stream_mock)
        self.assertTrue(ingest_result)
        
        metrics = tracker.get_metrics(repo_id)
        self.assertGreaterEqual(metrics["total"], 2)
        self.assertIn(selected_severity, metrics["breakdown"])
        
        resolver_name = f"system-resolver-{uuid.uuid4()}"
        resolution_notes = f"Resolved by automated pipeline {uuid.uuid4()}"
        resolved_status = tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolved_status)
        
        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)
        
        global_track_id = track_incident(
            repo_id=repo_id,
            incident_type="GLOBAL_TEST_ANOMALY",
            severity="INFO",
            description=f"Global tracker verification {uuid.uuid4()}"
        )
        self.assertIsNotNone(global_track_id)

if __name__ == "__main__":
    unittest.main()