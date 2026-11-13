import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from datetime import datetime

from skills.repo_health_incident_tracker import (
    RepoHealthIncidentTracker,
    track_incident,
    _GLOBAL_TRACKER
)

class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = uuid.uuid4().hex

    def test_track_incident_basic(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        self.assertIsNotNone(incident_id)
        
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.incident_type)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["status"], "OPEN")
        self.assertIsNone(incident["resolver"])
        self.assertIsNone(incident["resolution_notes"])
        self.assertIn("timestamp", incident)

    def test_track_incident_with_metadata(self):
        metadata = {uuid.uuid4().hex: uuid.uuid4().hex}
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=metadata
        )
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["metadata"], metadata)

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
        invalid_stream = random.randint(1000, 9999)
        result = self.tracker.ingest_anomaly_stream(invalid_stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_empty(self):
        stream = io.BytesIO(b"")
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_bad_json(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_missing_fields(self):
        payload = {
            "level": self.severity,
            "details": self.description
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_resolve_incident(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        resolver = uuid.uuid4().hex
        resolution_notes = uuid.uuid4().hex

        success = self.tracker.resolve_incident(incident_id, resolver, resolution_notes)
        self.assertTrue(success)

        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver)
        self.assertEqual(incident["resolution_notes"], resolution_notes)

    def test_resolve_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        success = self.tracker.resolve_incident(fake_id, uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(success)

    def test_get_incident_metrics(self):
        sev1 = uuid.uuid4().hex
        sev2 = uuid.uuid4().hex
        
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev1, uuid.uuid4().hex)
        self.tracker.track_incident(self.repo_id, uuid.uuid4().hex, sev2, uuid.uuid4().hex)

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev1], 2)
        self.assertEqual(metrics["breakdown"][sev2], 1)

    def test_get_metrics_filtered_and_global(self):
        repo_a = uuid.uuid4().hex
        repo_b = uuid.uuid4().hex
        sev = uuid.uuid4().hex

        self.tracker.track_incident(repo_a, uuid.uuid4().hex, sev, uuid.uuid4().hex)
        self.tracker.track_incident(repo_b, uuid.uuid4().hex, sev, uuid.uuid4().hex)

        metrics_a = self.tracker.get_metrics(repo_a)
        self.assertEqual(metrics_a["total"], 1)

        global_metrics = self.tracker.get_metrics()
        self.assertEqual(global_metrics["total"], 2)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/api/v1/collect"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], endpoint)
            self.assertIn("json", kwargs)

    def test_export_incident_failure(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.net/webhook"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

    def test_export_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.org/log"
        with patch("requests.post") as mock_post:
            result = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(result)
            mock_post.assert_not_called()

    def test_global_track_incident_wrapper(self):
        global_repo = uuid.uuid4().hex
        global_type = uuid.uuid4().hex
        global_sev = uuid.uuid4().hex
        global_desc = uuid.uuid4().hex

        incident_id = track_incident(
            repo_id=global_repo,
            incident_type=global_type,
            severity=global_sev,
            description=global_desc
        )
        self.assertIsNotNone(incident_id)
        incident = _GLOBAL_TRACKER.get_incident(incident_id)
        self.assertEqual(incident["repo_id"], global_repo)
        self.assertEqual(incident["incident_type"], global_type)