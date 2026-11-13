import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string
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
        self.incident_type = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = ''.join(random.choices(string.ascii_letters + string.whitespace, k=30))
        self.metadata = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_track_incident_returns_valid_uuid(self):
        inc_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsInstance(inc_id, str)
        uuid.UUID(inc_id)

    def test_get_incident_retrieves_correct_data(self):
        inc_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        incident = self.tracker.get_incident(inc_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["id"], inc_id)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.incident_type)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["metadata"], self.metadata)
        self.assertEqual(incident["status"], "OPEN")
        self.assertIsNone(incident["resolver"])
        self.assertIsNone(incident["resolution_notes"])
        self.assertIn("timestamp", incident)

    def test_get_nonexistent_incident_returns_none(self):
        fake_id = uuid.uuid4().hex
        self.assertIsNone(self.tracker.get_incident(fake_id))

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

    def test_ingest_anomaly_stream_invalid_types(self):
        self.assertFalse(self.tracker.ingest_anomaly_stream(random.randint(1, 1000)))
        
        empty_stream = io.BytesIO(b"")
        self.assertFalse(self.tracker.ingest_anomaly_stream(empty_stream))

        bad_json_stream = io.BytesIO(b"not a json")
        self.assertFalse(self.tracker.ingest_anomaly_stream(bad_json_stream))

        missing_fields_stream = io.BytesIO(json.dumps({"repo_id": self.repo_id}).encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(missing_fields_stream))

    def test_list_incidents_by_repo(self):
        repo_1 = uuid.uuid4().hex
        repo_2 = uuid.uuid4().hex

        type_1 = uuid.uuid4().hex
        type_2 = uuid.uuid4().hex

        self.tracker.track_incident(repo_1, type_1, "LOW", "desc1")
        self.tracker.track_incident(repo_1, type_2, "HIGH", "desc2")
        self.tracker.track_incident(repo_2, type_1, "MEDIUM", "desc3")

        incidents_repo_1 = self.tracker.list_incidents_by_repo(repo_1)
        self.assertEqual(len(incidents_repo_1), 2)
        self.assertTrue(all(inc["repo_id"] == repo_1 for inc in incidents_repo_1))

        incidents_repo_2 = self.tracker.list_incidents_by_repo(repo_2)
        self.assertEqual(len(incidents_repo_2), 1)
        self.assertEqual(incidents_repo_2[0]["repo_id"], repo_2)

    def test_resolve_incident(self):
        inc_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )

        resolver_name = uuid.uuid4().hex
        resolution_notes = uuid.uuid4().hex

        res = self.tracker.resolve_incident(inc_id, resolver_name, resolution_notes)
        self.assertTrue(res)

        incident = self.tracker.get_incident(inc_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver_name)
        self.assertEqual(incident["resolution_notes"], resolution_notes)

    def test_resolve_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        res = self.tracker.resolve_incident(fake_id, "Nobody", "Notes")
        self.assertFalse(res)

    def test_get_metrics_per_repo(self):
        repo_target = uuid.uuid4().hex
        self.tracker.track_incident(repo_target, "typeA", "HIGH", "d1")
        self.tracker.track_incident(repo_target, "typeB", "HIGH", "d2")
        self.tracker.track_incident(repo_target, "typeC", "LOW", "d3")
        
        other_repo = uuid.uuid4().hex
        self.tracker.track_incident(other_repo, "typeA", "CRITICAL", "d4")

        metrics = self.tracker.get_metrics(repo_target)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"], {"HIGH": 2, "LOW": 1})

    def test_get_metrics_global(self):
        repo_1 = uuid.uuid4().hex
        repo_2 = uuid.uuid4().hex
        self.tracker.track_incident(repo_1, "typeA", "HIGH", "d1")
        self.tracker.track_incident(repo_2, "typeB", "MEDIUM", "d2")

        metrics = self.tracker.get_metrics()
        self.assertEqual(metrics["total"], 2)
        self.assertEqual(metrics["breakdown"], {"HIGH": 1, "MEDIUM": 1})

    def test_export_incident(self):
        inc_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.tracker.export_incident(inc_id, endpoint)
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], endpoint)
            self.assertEqual(called_kwargs["json"]["id"], inc_id)

    def test_export_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        with patch("requests.post") as mock_post:
            result = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(result)
            mock_post.assert_not_called()

    def test_global_track_incident_wrapper(self):
        inc_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsInstance(inc_id, str)
        incident = _GLOBAL_TRACKER.get_incident(inc_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], self.repo_id)

if __name__ == "__main__":
    unittest.main()