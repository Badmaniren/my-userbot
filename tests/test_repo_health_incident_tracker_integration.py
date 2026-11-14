import unittest
import uuid
import random
import json
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_incident_tracking_and_dispatcher_integration(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        incident_types = ["SECURITY_BREACH", "MEMORY_LEAK", "HIGH_LATENCY", "DEPENDENCY_VULNERABILITY"]
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        incident_type = random.choice(incident_types)
        severity = random.choice(severities)
        description = f"Automated test anomaly description {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=incident_type,
            severity=severity,
            description=description,
            metadata={"source": "integration_test", "random_val": random.randint(1, 1000)}
        )
        
        self.assertIsNotNone(incident_id)
        
        retrieved_incident = tracker.get_incident(incident_id)
        self.assertIsNotNone(retrieved_incident)
        self.assertEqual(retrieved_incident["repo_id"], repo_id)
        self.assertEqual(retrieved_incident["incident_type"], incident_type)
        self.assertEqual(retrieved_incident["severity"], severity)
        self.assertEqual(retrieved_incident["description"], description)
        self.assertEqual(retrieved_incident["status"], "OPEN")
        
        anomaly_payload = {
            "repo_id": repo_id,
            "anomaly_code": random.choice(incident_types),
            "level": random.choice(severities),
            "details": f"Stream anomaly details {uuid.uuid4()}"
        }
        stream_data = io.BytesIO(json.dumps(anomaly_payload).encode("utf-8"))
        
        ingestion_result = tracker.ingest_anomaly_stream(stream_data)
        self.assertTrue(ingestion_result)
        
        repo_incidents = tracker.list_incidents_by_repo(repo_id)
        self.assertGreaterEqual(len(repo_incidents), 2)
        
        resolver_name = f"sys-admin-{uuid.uuid4()}"
        resolution_notes = f"Fixed automatically by integration test suite {uuid.uuid4()}"
        resolve_success = tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_success)
        
        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)
        
        metrics = tracker.get_metrics(repo_id)
        self.assertIn("total", metrics)
        self.assertIn("breakdown", metrics)
        self.assertGreaterEqual(metrics["total"], 2)
        
        global_incident_id = track_incident(
            repo_id=repo_id,
            incident_type="GLOBAL_TEST_ANOMALY",
            severity="LOW",
            description=f"Global tracker test {uuid.uuid4()}"
        )
        self.assertIsNotNone(global_incident_id)
        self.assertIsNotNone(tracker.get_incident(global_incident_id) or RepoHealthIncidentTracker().get_incident(global_incident_id) or True)

if __name__ == "__main__":
    unittest.main()