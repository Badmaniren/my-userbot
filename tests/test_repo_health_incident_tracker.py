import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.repo_health_incident_tracker import (
    RepoHealthIncidentTracker,
    track_incident,
    _default_tracker
)

class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = ''.join(random.choices(string.ascii_letters + string.whitespace, k=30))
        self.metadata = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}

    def test_track_incident_and_get(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsInstance(incident_id, str)
        
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["id"], incident_id)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.incident_type)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["metadata"], self.metadata)
        self.assertEqual(incident["status"], "OPEN")
        self.assertIsNone(incident["resolver"])
        self.assertIsNone(incident["resolution_notes"])
        self.assertIn("timestamp", incident)

    def test_track_incident_default_metadata(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["metadata"], {})

    def test_get_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        self.assertIsNone(self.tracker.get_incident(fake_id))

    def test_ingest_anomaly_stream_valid(self):
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type,
            "level": self.severity,
            "details": self.description
        }
        stream_data = io.BytesIO(json.dumps(payload).encode("utf-8"))
        
        result = self.tracker.ingest_anomaly_stream(stream_data)
        self.assertTrue(result)
        
        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.incident_type)
        self.assertEqual(incidents[0]["severity"], self.severity)
        self.assertEqual(incidents[0]["description"], self.description)

    def test_ingest_anomaly_stream_invalid_types_and_empty(self):
        self.assertFalse(self.tracker.ingest_anomaly_stream(random.randint(1, 1000)))
        
        empty_stream = io.BytesIO(b"")
        self.assertFalse(self.tracker.ingest_anomaly_stream(empty_stream))
        
        bad_json_stream = io.BytesIO(b"not a json")
        self.assertFalse(self.tracker.ingest_anomaly_stream(bad_json_stream))
        
        missing_fields = io.BytesIO(json.dumps({"repo_id": self.repo_id}).encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(missing_fields))

    def test_list_incidents_by_repo(self):
        repo_1 = uuid.uuid4().hex
        repo_2 = uuid.uuid4().hex
        
        id1 = self.tracker.track_incident(repo_1, self.incident_type, self.severity, self.description)
        id2 = self.tracker.track_incident(repo_1, self.incident_type, self.severity, self.description)
        id3 = self.tracker.track_incident(repo_2, self.incident_type, self.severity, self.description)
        
        list_repo_1 = self.tracker.list_incidents_by_repo(repo_1)
        self.assertEqual(len(list_repo_1), 2)
        retrieved_ids = [inc["id"] for inc in list_repo_1]
        self.assertIn(id1, retrieved_ids)
        self.assertIn(id2, retrieved_ids)
        self.assertNotIn(id3, retrieved_ids)

    def test_resolve_incident(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        resolver_name = uuid.uuid4().hex
        notes = uuid.uuid4().hex
        
        res = self.tracker.resolve_incident(incident_id, resolver_name, notes)
        self.assertTrue(res)
        
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver_name)
        self.assertEqual(incident["resolution_notes"], notes)

    def test_resolve_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        res = self.tracker.resolve_incident(fake_id, uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(res)

    def test_get_incident_metrics(self):
        sev1 = "HIGH"
        sev2 = "LOW"
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev2, uuid.uuid4().hex)
        
        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev1], 2)
        self.assertEqual(metrics["breakdown"][sev2], 1)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        
        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], endpoint)
            self.assertEqual(called_kwargs["json"]["id"], incident_id)

    def test_export_incident_failure_status(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        
        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

    def test_export_incident_request_exception(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        
        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException()
            
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

    def test_export_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            result = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(result)
            mock_post.assert_not_called()

    def test_module_level_track_incident(self):
        with patch.object(_default_tracker, "track_incident", return_value=uuid.uuid4().hex) as mock_track:
            res = track_incident(self.repo_id, self.incident_type, self.severity, self.description, self.metadata)
            mock_track.assert_called_once_with(
                self.repo_id, self.incident_type, self.severity, self.description, self.metadata
            )
            self.assertIsNotNone(res)

if __name__ == "__main__":
    unittest.main()