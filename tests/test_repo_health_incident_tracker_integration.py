import unittest
import uuid
import random
import json
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):

    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.incident_types = ["SECURITY_BREACH", "MEMORY_LEAK", "DEPENDENCY_FAILURE", "DISK_FULL"]
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_full_incident_lifecycle_and_metrics(self):
        random_type = random.choice(self.incident_types)
        random_severity = random.choice(self.severities)
        unique_description = f"Automated test incident description {uuid.uuid4()}"
        meta_key = f"key_{uuid.uuid4()}"
        meta_val = str(uuid.uuid4())
        metadata = {meta_key: meta_val}

        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=random_type,
            severity=random_severity,
            description=unique_description,
            metadata=metadata
        )

        self.assertIsNotNone(incident_id)
        
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["id"], incident_id)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], random_type)
        self.assertEqual(incident["severity"], random_severity)
        self.assertEqual(incident["description"], unique_description)
        self.assertEqual(incident["metadata"], metadata)
        self.assertEqual(incident["status"], "OPEN")

        metrics_before = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics_before["total"], 1)
        self.assertEqual(metrics_before["breakdown"].get(random_severity), 1)

        resolver_name = f"resolver-{uuid.uuid4()}"
        resolution_notes = f"Fixed via automated patch {uuid.uuid4()}"
        resolved = self.tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolved)

        updated_incident = self.tracker.get_incident(incident_id)
        self.assertEqual(updated_incident["status"], "RESOLVED")
        self.assertEqual(updated_incident["resolver"], resolver_name)
        self.assertEqual(updated_incident["resolution_notes"], resolution_notes)

    def test_ingest_anomaly_stream_integration(self):
        anomaly_code = f"ANOMALY_{uuid.uuid4().hex[:8].upper()}"
        level = random.choice(self.severities)
        details = f"Anomaly stream details {uuid.uuid4()}"
        
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": anomaly_code,
            "level": level,
            "details": details
        }
        
        stream_data = json.dumps(payload).encode("utf-8")
        stream = io.BytesIO(stream_data)

        success = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(success)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertTrue(len(incidents) > 0)
        
        matched_incident = next((inc for inc in incidents if inc["incident_type"] == anomaly_code), None)
        self.assertIsNotNone(matched_incident)
        self.assertEqual(matched_incident["severity"], level)
        self.assertEqual(matched_incident["description"], details)

    def test_global_tracker_functions(self):
        random_type = random.choice(self.incident_types)
        random_severity = random.choice(self.severities)
        desc = f"Global track test {uuid.uuid4()}"
        
        incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=random_type,
            severity=random_severity,
            description=desc
        )
        
        self.assertIsNotNone(incident_id)

if __name__ == "__main__":
    unittest.main()