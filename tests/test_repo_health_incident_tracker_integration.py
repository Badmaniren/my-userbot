import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_incident_lifecycle_and_ingestion_integration(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        anomaly_code = f"ERR-{random.randint(100, 999)}"
        level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"Random incident detail message {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=anomaly_code,
            severity=level,
            description=details,
            metadata={"source": "integration_test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        fetched_incident = tracker.get_incident(incident_id)
        self.assertIsNotNone(fetched_incident)
        self.assertEqual(fetched_incident["id"], incident_id)
        self.assertEqual(fetched_incident["repo_id"], repo_id)
        self.assertEqual(fetched_incident["incident_type"], anomaly_code)
        self.assertEqual(fetched_incident["severity"], level)
        self.assertEqual(fetched_incident["description"], details)
        self.assertEqual(fetched_incident["status"], "OPEN")
        
        resolver_name = f"admin-{uuid.uuid4()}"
        resolution_msg = f"Resolved via test {uuid.uuid4()}"
        resolve_success = tracker.resolve_incident(incident_id, resolver_name, resolution_msg)
        self.assertTrue(resolve_success)
        
        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_msg)
        
        stream_repo_id = f"repo-stream-{uuid.uuid4()}"
        stream_anomaly = f"STREAM-ERR-{random.randint(1000, 9999)}"
        stream_level = random.choice(["WARNING", "FATAL"])
        stream_details = f"Stream anomaly details {uuid.uuid4()}"
        
        raw_data = {
            "repo_id": stream_repo_id,
            "anomaly_code": stream_anomaly,
            "level": stream_level,
            "details": stream_details
        }
        
        file_stream = io.BytesIO(str(raw_data).replace("'", '"').encode('utf-8'))
        ingest_result = tracker.ingest_anomaly_stream(file_stream)
        self.assertTrue(ingest_result)
        
        stream_incidents = tracker.list_incidents_by_repo(stream_repo_id)
        self.assertEqual(len(stream_incidents), 1)
        self.assertEqual(stream_incidents[0]["incident_type"], stream_anomaly)
        self.assertEqual(stream_incidents[0]["severity"], stream_level)
        self.assertEqual(stream_incidents[0]["description"], stream_details)
        
        metrics = tracker.get_incident_metrics(stream_repo_id)
        self.assertEqual(metrics["total"], 1)
        self.assertIn(stream_level, metrics["breakdown"])
        self.assertEqual(metrics["breakdown"][stream_level], 1)
        
        standalone_repo_id = f"repo-standalone-{uuid.uuid4()}"
        standalone_id = track_incident(
            repo_id=standalone_repo_id,
            incident_type="STANDALONE_TEST",
            severity="LOW",
            description="Testing standalone function wrapper"
        )
        self.assertIsNotNone(standalone_id)

if __name__ == "__main__":
    unittest.main()