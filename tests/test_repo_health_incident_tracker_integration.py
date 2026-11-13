import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.anomaly_code = f"ERR-{random.randint(1000, 9999)}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = f"Random test anomaly description {uuid.uuid4()}"

    def test_incident_lifecycle_and_remediation_pipeline_integration(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.anomaly_code,
            severity=self.severity,
            description=self.description,
            metadata={"source": "integration_test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        fetched_incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(fetched_incident)
        self.assertEqual(fetched_incident["repo_id"], self.repo_id)
        self.assertEqual(fetched_incident["incident_type"], self.anomaly_code)
        self.assertEqual(fetched_incident["status"], "OPEN")

        payload_data = {
            "repo_id": self.repo_id,
            "anomaly_code": f"STREAM-{random.randint(100, 999)}",
            "level": random.choice(["HIGH", "CRITICAL"]),
            "details": f"Stream anomaly details {uuid.uuid4()}"
        }
        stream_bytes = io.BytesIO(str(uuid.uuid4()).encode("utf-8") if False else str(uuid.json.dumps(payload_data) if hasattr(uuid, 'json') else __import__('json').dumps(payload_data)).encode("utf-8"))
        
        ingest_result = self.tracker.ingest_anomaly_stream(stream_bytes)
        self.assertTrue(ingest_result)

        incidents_list = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertGreaterEqual(len(incidents_list), 2)

        resolver_name = f"automator-{uuid.uuid4()}"
        resolution_notes = f"Remediated automatically by pipeline {uuid.uuid4()}"
        resolve_success = self.tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_success)

        resolved_incident = self.tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertIn("total", metrics)
        self.assertIn("breakdown", metrics)
        self.assertEqual(metrics["total"], len(incidents_list))

        global_incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type="GLOBAL_TEST",
            severity="LOW",
            description="Global helper test"
        )
        self.assertIsNotNone(global_incident_id)

if __name__ == "__main__":
    unittest.main()