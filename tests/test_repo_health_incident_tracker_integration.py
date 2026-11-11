import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_incident_lifecycle_and_anomaly_ingestion(self):
        tracker = RepoHealthIncidentTracker()
        
        random_repo_id = f"repo-{uuid.uuid4()}"
        random_anomaly_code = f"ERR_CODE_{random.randint(1000, 9999)}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_description = f"Automated test anomaly description {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=random_repo_id,
            incident_type=random_anomaly_code,
            severity=random_severity,
            description=random_description,
            metadata={"source": "integration_test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        fetched_incident = tracker.get_incident(incident_id)
        self.assertIsNotNone(fetched_incident)
        self.assertEqual(fetched_incident["id"], incident_id)
        self.assertEqual(fetched_incident["repo_id"], random_repo_id)
        self.assertEqual(fetched_incident["incident_type"], random_anomaly_code)
        self.assertEqual(fetched_incident["severity"], random_severity)
        self.assertEqual(fetched_incident["description"], random_description)
        self.assertEqual(fetched_incident["status"], "OPEN")
        
        stream_data = {
            "repo_id": random_repo_id,
            "anomaly_code": f"STREAM_{random_anomaly_code}",
            "level": random_severity,
            "details": f"Streamed details {uuid.uuid4()}"
        }
        file_stream = io.BytesIO(str(stream_data).replace("'", '"').encode('utf-8'))
        
        ingest_result = tracker.ingest_anomaly_stream(file_stream)
        self.assertTrue(ingest_result)
        
        incidents = tracker.list_incidents_by_repo(random_repo_id)
        self.assertEqual(len(incidents), 2)
        
        resolver_name = f"resolver-{uuid.uuid4()}"
        resolution_notes = f"Fixed via integration test {uuid.uuid4()}"
        resolve_result = tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_result)
        
        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)
        
        metrics = tracker.get_incident_metrics(random_repo_id)
        self.assertEqual(metrics["total"], 2)
        self.assertIn(random_severity, metrics["breakdown"])
        
        global_incident_id = track_incident(
            repo_id=random_repo_id,
            incident_type="GLOBAL_TEST",
            severity="LOW",
            description="Testing module-level function"
        )
        self.assertIsNotNone(global_incident_id)

if __name__ == '__main__':
    unittest.main()