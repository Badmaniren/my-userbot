import unittest
import uuid
import random
import json
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_incident_lifecycle_and_integration(self):
        tracker = RepoHealthIncidentTracker()
        
        rand_repo_id = f"repo-{uuid.uuid4()}"
        rand_incident_type = f"ANOMALY_{random.randint(1000, 9999)}"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_description = f"Automated test incident description {uuid.uuid4()}"
        rand_metadata = {"env": "integration-test", "node_id": random.randint(1, 100)}

        incident_id = tracker.track_incident(
            repo_id=rand_repo_id,
            incident_type=rand_incident_type,
            severity=rand_severity,
            description=rand_description,
            metadata=rand_metadata
        )

        self.assertIsNotNone(incident_id)
        self.assertIsInstance(incident_id, str)

        retrieved = tracker.get_incident(incident_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], incident_id)
        self.assertEqual(retrieved["repo_id"], rand_repo_id)
        self.assertEqual(retrieved["incident_type"], rand_incident_type)
        self.assertEqual(retrieved["severity"], rand_severity)
        self.assertEqual(retrieved["description"], rand_description)
        self.assertEqual(retrieved["metadata"], rand_metadata)
        self.assertEqual(retrieved["status"], "OPEN")

        stream_data = json.dumps({
            "repo_id": rand_repo_id,
            "anomaly_code": f"STREAM_{rand_incident_type}",
            "level": rand_severity,
            "details": f"Stream details {uuid.uuid4()}"
        }).encode("utf-8")
        
        stream_io = io.BytesIO(stream_data)
        ingest_result = tracker.ingest_anomaly_stream(stream_io)
        self.assertTrue(ingest_result)

        incidents_list = tracker.list_incidents_by_repo(rand_repo_id)
        self.assertGreaterEqual(len(incidents_list), 2)

        metrics = tracker.get_metrics(rand_repo_id)
        self.assertIn("total", metrics)
        self.assertIn("breakdown", metrics)
        self.assertEqual(metrics["total"], len(incidents_list))

        resolver_name = f"admin-{uuid.uuid4()}"
        resolution_notes = f"Fixed via integration test {uuid.uuid4()}"
        resolve_result = tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_result)

        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)

        global_incident_id = track_incident(
            repo_id=rand_repo_id,
            incident_type="GLOBAL_TEST",
            severity="LOW",
            description="Global helper test"
        )
        self.assertIsNotNone(global_incident_id)
        self.assertIsInstance(global_incident_id, str)

if __name__ == "__main__":
    unittest.main()