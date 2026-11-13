import unittest
import uuid
import json
import io
import random
import string
from unittest.mock import patch, MagicMock
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker

class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.description = "".join(random.choices(string.ascii_letters, k=20))

    def test_track_and_get_incident(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, "ANOMALY", self.severity, self.description
        )
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["status"], "OPEN")

    def test_ingest_anomaly_stream_valid(self):
        payload = {
            "repo_id": uuid.uuid4().hex,
            "anomaly_code": uuid.uuid4().hex,
            "level": random.choice(["INFO", "WARN"]),
            "details": uuid.uuid4().hex
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(result)
        incidents = self.tracker.list_incidents_by_repo(payload["repo_id"])
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], payload["anomaly_code"])

    def test_ingest_anomaly_stream_invalid_data(self):
        stream = io.BytesIO(b"invalid_json_content")
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_resolve_incident(self):
        incident_id = self.tracker.track_incident(self.repo_id, "TYPE", "LOW", "DESC")
        resolver = uuid.uuid4().hex
        notes = uuid.uuid4().hex
        result = self.tracker.resolve_incident(incident_id, resolver, notes)
        self.assertTrue(result)
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver)
        self.assertEqual(incident["resolution_notes"], notes)

    def test_get_incident_metrics(self):
        repo_id = uuid.uuid4().hex
        severities = ["HIGH", "HIGH", "LOW"]
        for sev in severities:
            self.tracker.track_incident(repo_id, "TYPE", sev, "DESC")
        
        metrics = self.tracker.get_incident_metrics(repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"]["HIGH"], 2)
        self.assertEqual(metrics["breakdown"]["LOW"], 1)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(self.repo_id, "TYPE", "HIGH", "DESC")
        endpoint = f"https://{uuid.uuid4().hex}.com/api"
        
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs["json"]["id"], incident_id)

    def test_export_incident_failure(self):
        incident_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/api"
        
        with patch("requests.post") as mock_post:
            mock_post.side_effect = Exception("Network Error")
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()