import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = uuid.uuid4().hex
        self.metadata = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_track_incident_creates_and_returns_id(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsNotNone(incident_id)
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.incident_type)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["metadata"], self.metadata)
        self.assertEqual(incident["status"], "OPEN")

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
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(result)
        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.incident_type)

    def test_ingest_anomaly_stream_invalid_type(self):
        stream = random.randint(1000, 9999)
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_empty_data(self):
        stream = io.BytesIO(b"")
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_missing_fields(self):
        payload = {
            "repo_id": self.repo_id
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_list_incidents_by_repo(self):
        id1 = self.tracker.track_incident(self.repo_id, self.incident_type, self.severity, self.description)
        other_repo = uuid.uuid4().hex
        id2 = self.tracker.track_incident(other_repo, self.incident_type, self.severity, self.description)
        
        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["id"], id1)

    def test_resolve_incident(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        resolver = uuid.uuid4().hex
        notes = uuid.uuid4().hex
        result = self.tracker.resolve_incident(incident_id, resolver, notes)
        self.assertTrue(result)

        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver)
        self.assertEqual(incident["resolution_notes"], notes)

    def test_resolve_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        result = self.tracker.resolve_incident(fake_id, uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(result)

    def test_get_incident_metrics(self):
        sev1 = "HIGH"
        sev2 = "LOW"
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, self.description)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, self.description)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev2, self.description)

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev1], 2)
        self.assertEqual(metrics["breakdown"][sev2], 1)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            res = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(res)
            mock_post.assert_called_once()

    def test_export_incident_failure(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            res = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(res)

    def test_export_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        with patch("requests.post") as mock_post:
            res = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(res)
            mock_post.assert_not_called()

    def test_module_level_track_incident(self):
        incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsNotNone(incident_id)