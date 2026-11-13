import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class IntegrationTestRepoHealthIncidentTracker(unittest.TestCase):
    def test_incident_lifecycle_and_anomaly_ingestion(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        incident_type = f"ERR-{random.randint(100, 999)}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        description = f"Automated test anomaly description {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=incident_type,
            severity=severity,
            description=description,
            metadata={"source": "integration_test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        fetched_incident = tracker.get_incident(incident_id)
        self.assertIsNotNone(fetched_incident)
        self.assertEqual(fetched_incident["repo_id"], repo_id)
        self.assertEqual(fetched_incident["incident_type"], incident_type)
        self.assertEqual(fetched_incident["severity"], severity)
        self.assertEqual(fetched_incident["description"], description)
        self.assertEqual(fetched_incident["status"], "OPEN")
        
        payload_data = {
            "repo_id": repo_id,
            "anomaly_code": f"STREAM-{random.randint(1000, 9999)}",
            "level": random.choice(["WARNING", "ERROR"]),
            "details": f"Stream anomaly details {uuid.uuid4()}"
        }
        stream = io.BytesIO(str(payload_data).replace("'", '"').encode("utf-8"))
        
        ingestion_result = tracker.ingest_anomaly_stream(stream)
        self.assertTrue(ingestion_result)
        
        incidents_list = tracker.list_incidents_by_repo(repo_id)
        self.assertGreaterEqual(len(incidents_list), 2)
        
        resolver_name = f"bot-{uuid.uuid4()}"
        resolution_notes = f"Fixed automatically by remediation cycle {uuid.uuid4()}"
        resolve_result = tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_result)
        
        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)
        
        metrics = tracker.get_incident_metrics(repo_id)
        self.assertIn("total", metrics)
        self.assertIn("breakdown", metrics)
        self.assertGreaterEqual(metrics["total"], 2)
        
        global_tracked_id = track_incident(
            repo_id=repo_id,
            incident_type="GLOBAL_TEST",
            severity="LOW",
            description="Global function test"
        )
        self.assertIsNotNone(global_tracked_id)

if __name__ == "__main__":
    unittest.main()