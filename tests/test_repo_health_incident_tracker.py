import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
import string
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

def generate_random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = generate_random_string(8)
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = generate_random_string(20)

    def test_track_incident_and_get(self):
        meta_key = generate_random_string(5)
        meta_val = generate_random_string(5)
        metadata = {meta_key: meta_val}
        
        inc_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=metadata
        )
        
        self.assertIsInstance(inc_id, str)
        self.assertTrue(len(inc_id) > 0)
        
        incident = self.tracker.get_incident(inc_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["id"], inc_id)
        self.assertEqual(incident["repo_id"], self.repo_id)
        self.assertEqual(incident["incident_type"], self.incident_type)
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["description"], self.description)
        self.assertEqual(incident["metadata"], metadata)
        self.assertEqual(incident["status"], "OPEN")
        self.assertIsNone(incident["resolver"])
        self.assertIsNone(incident["resolution_notes"])
        self.assertIn("timestamp", incident)

    def test_track_incident_default_metadata(self):
        inc_id = self.tracker.track_incident(
            self.repo_id,
            self.incident_type,
            self.severity,
            self.description
        )
        incident = self.tracker.get_incident(inc_id)
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
        self.assertFalse(self.tracker.ingest_anomaly_stream(random.randint(100, 999)))
        self.assertFalse(self.tracker.ingest_anomaly_stream(None))

    def test_ingest_anomaly_stream_no_read_attr(self):
        class BadStream:
            pass
        self.assertFalse(self.tracker.ingest_anomaly_stream(BadStream()))

    def test_ingest_anomaly_stream_empty_data(self):
        stream = io.BytesIO(b"")
        self.assertFalse(self.tracker.ingest_anomaly_stream(stream))

    def test_ingest_anomaly_stream_invalid_json(self):
        stream = io.BytesIO(generate_random_string(15).encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(stream))

    def test_ingest_anomaly_stream_non_dict_payload(self):
        payload = [generate_random_string(5), generate_random_string(5)]
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(stream))

    def test_ingest_anomaly_stream_missing_required_fields(self):
        payload = {
            "repo_id": self.repo_id
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(stream))

    def test_list_incidents_by_repo(self):
        other_repo_id = uuid.uuid4().hex
        self.tracker.track_incident(self.repo_id, self.incident_type, self.severity, self.description)
        self.tracker.track_incident(self.repo_id, generate_random_string(5), "LOW", generate_random_string(5))
        self.tracker.track_incident(other_repo_id, generate_random_string(5), "HIGH", generate_random_string(5))

        repo_incidents = self.tracker.list_incidents_by_repo(self.repo_id)
        self.assertEqual(len(repo_incidents), 2)
        for inc in repo_incidents:
            self.assertEqual(inc["repo_id"], self.repo_id)

    def test_resolve_incident(self):
        inc_id = self.tracker.track_incident(
            self.repo_id,
            self.incident_type,
            self.severity,
            self.description
        )
        resolver_name = generate_random_string(6)
        notes = generate_random_string(12)

        res = self.tracker.resolve_incident(inc_id, resolver_name, notes)
        self.assertTrue(res)

        incident = self.tracker.get_incident(inc_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver_name)
        self.assertEqual(incident["resolution_notes"], notes)

    def test_resolve_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        res = self.tracker.resolve_incident(fake_id, generate_random_string(), generate_random_string())
        self.assertFalse(res)

    def test_get_incident_metrics(self):
        sev1 = generate_random_string(4).upper()
        sev2 = generate_random_string(4).upper()
        self.tracker.track_incident(self.repo_id, generate_random_string(), sev1, generate_random_string())
        self.tracker.track_incident(self.repo_id, generate_random_string(), sev1, generate_random_string())
        self.tracker.track_incident(self.repo_id, generate_random_string(), sev2, generate_random_string())

        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev1], 2)
        self.assertEqual(metrics["breakdown"][sev2], 1)

    def test_get_metrics_global_and_repo(self):
        repo_a = uuid.uuid4().hex
        repo_b = uuid.uuid4().hex
        sev = "CRITICAL"
        self.tracker.track_incident(repo_a, generate_random_string(), sev, generate_random_string())
        self.tracker.track_incident(repo_b, generate_random_string(), sev, generate_random_string())

        global_metrics = self.tracker.get_metrics()
        self.assertEqual(global_metrics["total"], 2)
        self.assertEqual(global_metrics["breakdown"][sev], 2)

        repo_metrics = self.tracker.get_metrics(repo_a)
        self.assertEqual(repo_metrics["total"], 1)
        self.assertEqual(repo_metrics["breakdown"][sev], 1)

    def test_export_incident_success(self):
        inc_id = self.tracker.track_incident(
            self.repo_id,
            self.incident_type,
            self.severity,
            self.description
        )
        endpoint_url = f"http://{generate_random_string(6)}.com/{generate_random_string(4)}"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            success = self.tracker.export_incident(inc_id, endpoint_url)
            self.assertTrue(success)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], endpoint_url)
            self.assertIn("json", called_kwargs)
            self.assertEqual(called_kwargs["json"]["id"], inc_id)

    def test_export_incident_failure(self):
        inc_id = self.tracker.track_incident(
            self.repo_id,
            self.incident_type,
            self.severity,
            self.description
        )
        endpoint_url = f"http://{generate_random_string(6)}.com/{generate_random_string(4)}"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            success = self.tracker.export_incident(inc_id, endpoint_url)
            self.assertFalse(success)

    def test_export_nonexistent_incident(self):
        fake_id = uuid.uuid4().hex
        endpoint_url = f"http://{generate_random_string(6)}.com/"
        with patch("requests.post") as mock_post:
            success = self.tracker.export_incident(fake_id, endpoint_url)
            self.assertFalse(success)
            mock_post.assert_not_called()

    def test_track_alias_method(self):
        inc_id = self.tracker.track_(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        incident = self.tracker.get_incident(inc_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["id"], inc_id)

    def test_module_level_track_incident(self):
        inc_id = track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        self.assertIsInstance(inc_id, str)
        self.assertTrue(len(inc_id) > 0)