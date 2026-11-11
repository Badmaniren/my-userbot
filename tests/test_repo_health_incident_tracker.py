import io
import json
import random
import string
import unittest
import uuid
from unittest.mock import patch, MagicMock

import requests

from skills.repo_health_incident_tracker import (
    RepoHealthIncidentTracker,
    track_incident as top_level_track_incident,
)


def random_string(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_uuid_str():
    return str(uuid.uuid4())


class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()

    def test_track_incident_and_get_incident(self):
        repo_id = f"repo-{random_uuid_str()}"
        incident_type = f"ERR_{random_string(6).upper()}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL", random_string(5)])
        description = f"Incident desc: {random_string(20)}"
        metadata = {random_string(5): random_string(10), random_string(5): random.randint(1, 100)}

        incident_id = self.tracker.track_incident(
            repo_id=repo_id,
            incident_type=incident_type,
            severity=severity,
            description=description,
            metadata=metadata
        )

        self.assertIsInstance(incident_id, str)
        self.assertTrue(len(incident_id) > 0)

        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["id"], incident_id)
        self.assertEqual(incident["repo_id"], repo_id)
        self.assertEqual(incident["incident_type"], incident_type)
        self.assertEqual(incident["severity"], severity)
        self.assertEqual(incident["description"], description)
        self.assertEqual(incident["metadata"], metadata)
        self.assertEqual(incident["status"], "OPEN")
        self.assertIsNone(incident["resolver"])
        self.assertIsNone(incident["resolution_notes"])
        self.assertIn("timestamp", incident)

    def test_track_incident_default_metadata(self):
        repo_id = f"repo-{random_uuid_str()}"
        incident_type = random_string(8)
        severity = random_string(4)
        description = random_string(15)

        incident_id = self.tracker.track_incident(
            repo_id=repo_id,
            incident_type=incident_type,
            severity=severity,
            description=description
        )

        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["metadata"], {})

    def test_get_incident_not_found(self):
        non_existent_id = random_uuid_str()
        self.assertIsNone(self.tracker.get_incident(non_existent_id))

    def test_ingest_anomaly_stream_success(self):
        repo_id = f"repo-{random_uuid_str()}"
        anomaly_code = f"ANOMALY_{random_string(4).upper()}"
        level = random_string(6)
        details = f"Details {random_string(30)}"

        payload = {
            "repo_id": repo_id,
            "anomaly_code": anomaly_code,
            "level": level,
            "details": details
        }

        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(result)

        incidents = self.tracker.list_incidents_by_repo(repo_id)
        self.assertEqual(len(incidents), 1)
        inc = incidents[0]
        self.assertEqual(inc["repo_id"], repo_id)
        self.assertEqual(inc["incident_type"], anomaly_code)
        self.assertEqual(inc["severity"], level)
        self.assertEqual(inc["description"], details)

    def test_ingest_anomaly_stream_invalid_formats(self):
        empty_stream = io.BytesIO(b"")
        self.assertFalse(self.tracker.ingest_anomaly_stream(empty_stream))

        malformed_stream = io.BytesIO(f"{{bad_json: {random_string(5)}".encode("utf-8"))
        self.assertFalse(self.tracker.ingest_anomaly_stream(malformed_stream))

        invalid_bytes_stream = io.BytesIO(b"\x80\x81\xfe\xff")
        self.assertFalse(self.tracker.ingest_anomaly_stream(invalid_bytes_stream))

        self.assertFalse(self.tracker.ingest_anomaly_stream(random.randint(100, 999)))

    def test_list_incidents_by_repo(self):
        repo_1 = f"repo-{random_uuid_str()}"
        repo_2 = f"repo-{random_uuid_str()}"

        count_1 = random.randint(2, 5)
        count_2 = random.randint(2, 5)

        for _ in range(count_1):
            self.tracker.track_incident(repo_1, random_string(5), random_string(4), random_string(10))

        for _ in range(count_2):
            self.tracker.track_incident(repo_2, random_string(5), random_string(4), random_string(10))

        list_1 = self.tracker.list_incidents_by_repo(repo_1)
        list_2 = self.tracker.list_incidents_by_repo(repo_2)

        self.assertEqual(len(list_1), count_1)
        self.assertEqual(len(list_2), count_2)
        self.assertTrue(all(inc["repo_id"] == repo_1 for inc in list_1))
        self.assertTrue(all(inc["repo_id"] == repo_2 for inc in list_2))

    def test_resolve_incident(self):
        repo_id = f"repo-{random_uuid_str()}"
        inc_id = self.tracker.track_incident(repo_id, random_string(5), random_string(4), random_string(10))

        resolver = f"user_{random_string(6)}"
        notes = f"Fixed by {random_string(15)}"

        success = self.tracker.resolve_incident(inc_id, resolver, notes)
        self.assertTrue(success)

        updated_inc = self.tracker.get_incident(inc_id)
        self.assertEqual(updated_inc["status"], "RESOLVED")
        self.assertEqual(updated_inc["resolver"], resolver)
        self.assertEqual(updated_inc["resolution_notes"], notes)

        fake_id = random_uuid_str()
        self.assertFalse(self.tracker.resolve_incident(fake_id, resolver, notes))

    def test_get_incident_metrics(self):
        repo_id = f"repo-{random_uuid_str()}"
        sev_a = f"SEV_{random_string(4)}"
        sev_b = f"SEV_{random_string(4)}"

        count_a = random.randint(1, 4)
        count_b = random.randint(1, 4)

        for _ in range(count_a):
            self.tracker.track_incident(repo_id, random_string(5), sev_a, random_string(10))

        for _ in range(count_b):
            self.tracker.track_incident(repo_id, random_string(5), sev_b, random_string(10))

        metrics = self.tracker.get_incident_metrics(repo_id)

        self.assertEqual(metrics["total"], count_a + count_b)
        self.assertEqual(metrics["breakdown"].get(sev_a), count_a)
        self.assertEqual(metrics["breakdown"].get(sev_b), count_b)

    def test_export_incident(self):
        endpoint = f"https://{random_string(8)}.domain/api/v1/{random_string(6)}"

        self.assertFalse(self.tracker.export_incident(random_uuid_str(), endpoint))

        repo_id = f"repo-{random_uuid_str()}"
        inc_id = self.tracker.track_incident(repo_id, random_string(5), random_string(4), random_string(10))
        incident_data = self.tracker.get_incident(inc_id)

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            res = self.tracker.export_incident(inc_id, endpoint)

            self.assertTrue(res)
            mock_post.assert_called_once_with(endpoint, json=incident_data)

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            res = self.tracker.export_incident(inc_id, endpoint)
            self.assertFalse(res)

        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException(random_string(10))

            res = self.tracker.export_incident(inc_id, endpoint)
            self.assertFalse(res)

    def test_standalone_track_incident_function(self):
        repo_id = f"repo-{random_uuid_str()}"
        inc_type = random_string(6)
        sev = random_string(4)
        desc = random_string(12)

        inc_id = top_level_track_incident(repo_id, inc_type, sev, desc)
        self.assertIsInstance(inc_id, str)
        self.assertTrue(len(inc_id) > 0)


if __name__ == "__main__":
    unittest.main()