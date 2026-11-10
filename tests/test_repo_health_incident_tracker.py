import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import requests

from skills.repo_health_incident_tracker import (
    RepoHealthIncidentTracker,
    track_incident,
    _global_tracker
)

class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        letters = string.ascii_letters + " "
        self.description = ''.join(random.choices(letters, k=25)).strip()
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
        self.assertEqual(len(incident_id), 32)

        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.incident_type)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["metadata"], self.metadata)
        self.assertEqual(incident["status"], "OPEN")
        self.assertIsNone(incident["resolver"])
        self.assertIsNone(incident["resolution_notes"])

    def test_get_incident_retrieves_correct_data(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        fetched = self.tracker.get_incident(incident_id)
        self.assertEqual(fetched["id"], incident_id)
        self.assertEqual(fetched["repo_id"], self.repo_id)

        non_existent_id = uuid.uuid4().hex
        self.assertIsNone(self.tracker.get_incident(non_existent_id))

    def test_ingest_anomaly_stream_success(self):
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type,
            "level": self.severity,
            "details": self.description
        }
        stream_data = io.BytesIO(json.dumps(payload).encode('utf-8'))

        result = self.tracker.ingest_anomaly_stream(stream_data)
        self.assertTrue(result)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.incident_type)

    def test_ingest_anomaly_stream_invalid_json(self):
        random_bytes = uuid.uuid4().bytes
        stream_data = io.BytesIO(random_bytes)
        result = self.tracker.ingest_anomaly_stream(stream_data)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_empty_content(self):
        stream_data = io.BytesIO(b"")
        result = self.tracker.ingest_anomaly_stream(stream_data)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_missing_fields(self):
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type
        }
        stream_data = io.BytesIO(json.dumps(payload).encode('utf-8'))
        result = self.tracker.ingest_anomaly_stream(stream_data)
        self.assertFalse(result)

    def test_resolve_incident_success(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        resolver_name = uuid.uuid4().hex
        resolution_notes = uuid.uuid4().hex

        result = self.tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(result)

        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver_name)
        self.assertEqual(incident["resolution_notes"], resolution_notes)

    def test_resolve_incident_not_found(self):
        fake_id = uuid.uuid4().hex
        resolver_name = uuid.uuid4().hex
        resolution_notes = uuid.uuid4().hex
        result = self.tracker.resolve_incident(fake_id, resolver_name, resolution_notes)
        self.assertFalse(result)

    def test_get_incident_metrics(self):
        sev1 = self.severity
        sev2 = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, self.description)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, self.description)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev2, self.description)

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"].get(sev1, 0), 2)
        self.assertEqual(metrics["breakdown"].get(sev2, 0), 1)

        metrics_alias = self.tracker.get_metrics(self.repo_id)
        self.assertEqual(metrics_alias, metrics)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/api/webhook"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(result)
            mock_post.assert_called_once()

    def test_export_incident_not_found(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/api/webhook"
        with patch("requests.post") as mock_post:
            result = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(result)
            mock_post.assert_not_called()

    def test_export_incident_request_exception(self):
        incident_id = self.tracker.track_incident(
            self.repo_id, self.incident_type, self.severity, self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/api/webhook"

        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Network failure")
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

    def test_global_track_incident_wrapper(self):
        incident_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsInstance(incident_id, str)
        incident = _global_tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)