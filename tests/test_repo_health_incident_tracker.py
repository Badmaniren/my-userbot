import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from datetime import datetime
import requests

from skills.repo_health_incident_tracker import (
    RepoHealthIncidentTracker,
    track_incident as module_track_incident,
    _default_tracker
)

class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = f"anomaly_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = f"Desc {uuid.uuid4().hex}"
        self.metadata = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_track_incident_creates_and_stores(self):
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

    def test_list_incidents_by_repo(self):
        other_repo_id = uuid.uuid4().hex

        id1 = self.tracker.track_incident(self.repo_id, self.incident_type, self.severity, self.description)
        id2 = self.tracker.track_incident(self.repo_id, self.incident_type, self.severity, self.description)
        self.tracker.track_incident(other_repo_id, self.incident_type, self.severity, self.description)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 2)
        returned_ids = {inc["id"] for inc in incidents}
        self.assertEqual(returned_ids, {id1, id2})

    def test_resolve_incident_success(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
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

        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev2, uuid.uuid4().hex)

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev1], 2)
        self.assertEqual(metrics["breakdown"][sev2], 1)

    def test_ingest_anomaly_stream_success(self):
        payload = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type,
            "level": self.severity,
            "details": self.description
        }
        stream_data = json.dumps(payload).encode("utf-8")
        stream = io.BytesIO(stream_data)

        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(result)

        incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["incident_type"], self.incident_type)
        self.assertEqual(incidents[0]["severity"], self.severity)
        self.assertEqual(incidents[0]["description"], self.description)

    def test_ingest_anomaly_stream_invalid_type(self):
        result = self.tracker.ingest_anomaly_stream(random.randint(1, 100))
        self.assertFalse(result)

    def test_ingest_anomaly_stream_empty(self):
        stream = io.BytesIO(b"")
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_missing_required_fields(self):
        payload = {
            "level": self.severity,
            "details": self.description
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_exception_handling(self):
        bad_stream = MagicMock()
        bad_stream.read.side_effect = Exception(uuid.uuid4().hex)
        result = self.tracker.ingest_anomaly_stream(bad_stream)
        self.assertFalse(result)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/api/v1/report"

        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], endpoint)
            self.assertEqual(kwargs["json"]["id"], incident_id)

    def test_export_incident_not_found(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/api"
        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            result = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(result)
            mock_post.assert_not_called()

    def test_export_incident_request_failure(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/api"

        with patch("skills.repo_health_incident_tracker.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException(uuid.uuid4().hex)
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

    def test_module_level_track_incident(self):
        with patch.object(_default_tracker, "track_incident", return_value=uuid.uuid4().hex) as mock_track:
            res = module_track_incident(
                repo_id=self.repo_id,
                incident_type=self.incident_type,
                severity=self.severity,
                description=self.description,
                metadata=self.metadata
            )
            mock_track.assert_called_once_with(
                self.repo_id,
                self.incident_type,
                self.severity,
                self.description,
                self.metadata
            )
            self.assertIsNotNone(res)