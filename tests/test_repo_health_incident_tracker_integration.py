import unittest
import uuid
import random
import json
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = f"repo_{uuid.uuid4().hex[:8]}"
        self.incident_types = ["SYNTAX_ERROR", "MEMORY_LEAK", "SECURITY_VULN", "PERFORMANCE_DROP"]
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_full_incident_lifecycle_and_metrics_integration(self):
        random_type = random.choice(self.incident_types)
        random_severity = random.choice(self.severities)
        random_desc = f"Automated test incident description {uuid.uuid4().hex}"
        random_metadata = {"component": f"module_{random.randint(1, 100)}", "attempt": random.randint(1, 5)}

        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=random_type,
            severity=random_severity,
            description=random_desc,
            metadata=random_metadata
        )

        self.assertIsNotNone(incident_id)
        self.assertEqual(len(incident_id), 32)

        retrieved_incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(retrieved_incident)
        self.assertEqual(retrieved_incident["repo_id"], self.repo_id)
        self.assertEqual(retrieved_incident["incident_type"], random_type)
        self.assertEqual(retrieved_incident["severity"], random_severity)
        self.assertEqual(retrieved_incident["description"], random_desc)
        self.assertEqual(retrieved_incident["metadata"], random_metadata)
        self.assertEqual(retrieved_incident["status"], "OPEN")

        metrics = self.tracker.get_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 1)
        self.assertEqual(metrics["breakdown"][random_severity], 1)

        resolver_name = f"engineer_{uuid.uuid4().hex[:6]}"
        resolution_notes = f"Fixed by applying patch {uuid.uuid4().hex[:6]}"
        resolved_status = self.tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolved_status)

        updated_incident = self.tracker.get_incident(incident_id)
        self.assertEqual(updated_incident["status"], "RESOLVED")
        self.assertEqual(updated_incident["resolver"], resolver_name)
        self.assertEqual(updated_incident["resolution_notes"], resolution_notes)

    def test_ingest_anomaly_stream_integration(self):
        stream_payload = {
            "repo_id": self.repo_id,
            "anomaly_code": random.choice(self.incident_types),
            "level": random.choice(self.severities),
            "details": f"Stream anomaly detected at {uuid.uuid4().hex}"
        }
        
        stream_data = io.BytesIO(json.dumps(stream_payload).encode('utf-8'))
        
        ingestion_result = self.tracker.ingest_anomaly_stream(stream_data)
        self.assertTrue(ingestion_result)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["description"], stream_payload["details"])
        self.assertEqual(incidents[0]["incident_type"], stream_payload["anomaly_code"])

    def test_global_tracker_proxy_integration(self):
        random_type = random.choice(self.incident_types)
        random_severity = random.choice(self.severities)
        random_desc = f"Global tracker test {uuid.uuid4().hex}"

        global_incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=random_type,
            severity=random_severity,
            description=random_desc
        )

        self.assertIsNotNone(global_incident_id)
        self.assertEqual(len(global_incident_id), 32)

if __name__ == '__main__':
    unittest.main()