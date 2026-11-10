import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
from datetime import datetime

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
        self.assertIsInstance(incident_id, str)
        self.assertTrue(len(incident_id) > 0)

        stored = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored["id"], incident_id)
        self.assertEqual(stored["repo_id"], self.repo_id)
        self.assertEqual(stored["incident_type"], self.incident_type)
        self.assertEqual(stored["severity"], self.severity)
        self.assertEqual(stored["description"], self.description)
        self.assertEqual(stored["metadata"], self.metadata)
        self.assertEqual(stored["status"], "OPEN")
        self.assertIsNone(stored["resolver"])
        self.assertIsNone(stored["resolution_notes"])
        self.assertIn("timestamp", stored)

    def test_get_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        self.assertIsNone(self.tracker.get_incident(fake_id))

    def test_ingest_anomaly_stream_success(self):
        anomaly_data = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type,
            "level": self.severity,
            "details": self.description
        }
        stream = io.BytesIO(json.dumps(anomaly_data).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(result)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.incident_type)
        self.assertEqual(incidents[0]["severity"], self.severity)
        self.assertEqual(incidents[0]["description"], self.description)

    def test_ingest_anomaly_stream_empty(self):
        stream = io.BytesIO(b"")
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_invalid_json(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_list_incidents_by_repo(self):
        repo_1 = uuid.uuid4().hex
        repo_2 = uuid.uuid4().hex

        id1 = self.tracker.track_incident(repo_1, uuid.uuid4().hex, "LOW", uuid.uuid4().hex)
        id2 = self.tracker.track_incident(repo_1, uuid.uuid4().hex, "HIGH", uuid.uuid4().hex)
        id3 = self.tracker.track_incident(repo_2, uuid.uuid4().hex, "MEDIUM", uuid.uuid4().hex)

        incidents_repo_1 = self.tracker.list_incidents_by_repo(repo_1)
        self.assertEqual(len(incidents_repo_1), 2)
        retrieved_ids = {inc["id"] for inc in incidents_repo_1}
        self.assertEqual(retrieved_ids, {id1, id2})

        incidents_repo_2 = self.tracker.list_incidents_by_repo(repo_2)
        self.assertEqual(len(incidents_repo_2), 1)
        self.assertEqual(incidents_repo_2[0]["id"], id3)

    def test_resolve_incident_success(self):
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

    def test_resolve_incident_not_found(self):
        fake_id = uuid.uuid4().hex
        result = self.tracker.resolve_incident(fake_id, uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(result)

    def test_get_incident_metrics(self):
        sev_1 = "LOW"
        sev_2 = "HIGH"
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev_1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev_1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev_2, uuid.uuid4().hex)

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev_1], 2)
        self.assertEqual(metrics["breakdown"][sev_2], 1)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            success = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(success)
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["json"]["id"], incident_id)

    def test_export_incident_failure(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            success = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(success)

    def test_export_incident_not_found(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"

        with patch("requests.post") as mock_post:
            success = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(success)
            mock_post.assert_not_called()

    def test_module_level_track_incident(self):
        incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        self.assertIsInstance(incident_id, str)
        self.assertTrue(len(incident_id) > 0)