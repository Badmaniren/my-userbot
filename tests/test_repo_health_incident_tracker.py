import unittest
from unittest.mock import patch
import io
import json
import random
import uuid
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()
        self.repo_id = uuid.uuid4().hex
        self.incident_type = f"ERR_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.description = f"Desc_{uuid.uuid4().hex}"
        self.metadata = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_track_incident_returns_valid_id(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
        self.assertIsInstance(incident_id, str)
        uuid.UUID(incident_id)

    def test_get_incident_retrieves_correct_data(self):
        incident_id = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata=self.metadata
        )
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

    def test_get_nonexistent_incident(self):
        missing_id = str(uuid.uuid4())
        incident = self.tracker.get_incident(missing_id)
        self.assertIsNone(incident)

    def test_ingest_anomaly_stream_success(self):
        data = {
            "repo_id": self.repo_id,
            "anomaly_code": self.incident_type,
            "level": self.severity,
            "details": self.description
        }
        stream_content = json.dumps(data).encode('utf-8')
        file_stream = io.BytesIO(stream_content)

        result = self.tracker.ingest_anomaly_stream(file_stream)