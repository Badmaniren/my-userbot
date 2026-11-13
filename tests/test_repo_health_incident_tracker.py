import unittest
import json
import io
import uuid
import random
import requests
from unittest.mock import patch, MagicMock
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = uuid.uuid4().hex
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.description = uuid.uuid4().hex

    def test_track_and_get_incident(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        incident = self.tracker.get_incident(incident_id)
        
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["status"], "OPEN")
        self.assertEqual(incident["incident_type"], self.incident_type)

    def test_ingest_anomaly_stream_valid(self):
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type,
            "level": self.severity,
            "details": self.description
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        
        self.assertTrue(result)
        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["description"], self.description)

    def test_ingest_anomaly_stream_invalid_types_and_empty(self):
        # Test integer input
        self.assertFalse(self.tracker.ingest_anomaly_stream(12345))
        
        # Test missing fields
        payload = {"repo_id": self.repo_id}
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(stream))

    def test_resolve_incident(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        resolver = uuid.uuid4().hex
        notes = uuid.uuid4().hex
        
        result = self.tracker.resolve_incident(incident_id, resolver, notes)
        incident = self.tracker.get_incident(incident_id)
        
        self.assertTrue(result)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver)
        self.assertEqual(incident["resolution_notes"], notes)

    def test_get_incident_metrics(self):
        for _ in range(3):
            self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, "HIGH", "test")
        
        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"]["HIGH"], 3)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"http://{uuid.uuid4().hex}.com/api"
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            result = self.tracker.export_incident(incident_id, endpoint)
            
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs["json"]["id"], incident_id)

    def test_export_incident_request_exception(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"http://{uuid.uuid4().hex}.com/api"
        
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException()
            result = self.tracker.export_incident(incident_id, endpoint)
            
            self.assertFalse(result)

    def test_module_level_track_incident(self):
        # Testing the global _default_tracker wrapper
        incident_id = track_incident(self.repo_id, self.incident_type, self.severity, self.description)
        self.assertIsNotNone(incident_id)
        # Verify it exists in the global tracker
        from skills.repo_health_incident_tracker import _default_tracker
        self.assertIsNotNone(_default_tracker.get_incident(incident_id))

if __name__ == "__main__":
    unittest.main()