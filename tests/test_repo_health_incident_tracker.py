import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from datetime import datetime
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = f"anomaly_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = f"desc_{uuid.uuid4().hex}"
        self.metadata = {uuid.uuid4().hex: uuid.uuid4().hex}

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

    def test_track_incident_default_metadata(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["metadata"], {})

    def test_get_incident_nonexistent(self):
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
        invalid_stream = random.randint(1000, 9999)
        result = self.tracker.ingest_anomaly_stream(invalid_stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_empty_data(self):
        stream = io.BytesIO(b"")
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_malformed_json(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_ingest_anomaly_stream_missing_required_fields(self):
        payload = {"level": self.severity}
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

    def test_list_incidents_by_repo(self):
        repo_1 = uuid.uuid4().hex
        repo_2 = uuid.uuid4().hex
        id1 = self.tracker.track_incident(repo_1, self.incident_type, self.severity, self.description)
        id2 = self.tracker.track_incident(repo_1, self.incident_type, self.severity, self.description)
        id3 = self.tracker.track_incident(repo_2, self.incident_type, self.severity, self.description)
        
        incidents_1 = self.tracker.list_incidents_by_repo(repo_1)
        self.assertEqual(len(incidents_1), 2)
        self.assertIn(id1, [i["id"] for i in incidents_1])
        self.assertIn(id2, [i["id"] for i in incidents_1])

        incidents_2 = self.tracker.list_incidents_by_repo(repo_2)
        self.assertEqual(len(incidents_2), 1)
        self.assertEqual(incidents_2[0]["id"], id3)

    def test_resolve_incident(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        resolver = uuid.uuid4().hex
        resolution_notes = f"notes_{uuid.uuid4().hex}"
        
        result = self.tracker.resolve_incident(incident_id, resolver, resolution_notes)
        self.assertTrue(result)
        
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertEqual(incident["resolver"], resolver)
        self.assertEqual(incident["resolution_notes"], resolution_notes)

    def test_resolve_incident_nonexistent(self):
        fake_id = uuid.uuid4().hex
        resolver = uuid.uuid4().hex
        notes = uuid.uuid4().hex
        self.assertFalse(self.tracker.resolve_incident(fake_id, resolver, notes))

    def test_get_incident_metrics(self):
        sev1 = "HIGH"
        sev2 = "LOW"
        self.tracker.track_incident(self.repo_id, "type1", sev1, "desc")
        self.tracker.track_incident(self.repo_id, "type2", sev1, "desc")
        self.tracker.track_incident(self.repo_id, "type3", sev2, "desc")
        
        metrics = self.tracker.get_incident_metrics(self.repo_id)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["breakdown"][sev1], 2)
        self.assertEqual(metrics["breakdown"][sev2], 1)

    def test_get_metrics_global_and_filtered(self):
        repo_a = uuid.uuid4().hex
        repo_b = uuid.uuid4().hex
        self.tracker.track_incident(repo_a, "t1", "CRITICAL", "d")
        self.tracker.track_incident(repo_b, "t2", "LOW", "d")
        
        global_metrics = self.tracker.get_metrics()
        self.assertEqual(global_metrics["total"], 2)
        self.assertEqual(global_metrics["breakdown"]["CRITICAL"], 1)
        self.assertEqual(global_metrics["breakdown"]["LOW"], 1)
        
        filtered_metrics = self.tracker.get_metrics(repo_a)
        self.assertEqual(filtered_metrics["total"], 1)
        self.assertEqual(filtered_metrics["breakdown"]["CRITICAL"], 1)

    def test_export_incident_success(self):
        incident_id = self.tracker.track_incident(
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
            
            success = self.tracker.export_incident(incident_id, endpoint)
            self.assertTrue(success)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], endpoint)
            self.assertEqual(kwargs["json"]["id"], incident_id)

    def test_export_incident_failure(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description
        )
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            
            success = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(success)

    def test_export_incident_nonexistent(self):
        fake_id = uuid.uuid4().hex
        endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        with patch("requests.post") as mock_post:
            success = self.tracker.export_incident(fake_id, endpoint)
            self.assertFalse(success)
            mock_post.assert_not_called()

    def test_global_track_incident_function(self):
        r_id = uuid.uuid4().hex
        i_type = uuid.uuid4().hex
        sev = "MEDIUM"
        desc = uuid.uuid4().hex
        
        inc_id = track_incident(r_id, i_type, sev, desc)
        self.assertIsInstance(inc_id, str)