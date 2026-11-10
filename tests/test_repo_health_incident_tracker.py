import unittest
import uuid
import json
import io
import random
import string
import requests
from unittest.mock import patch, MagicMock
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker

class TestRepoHealthIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = RepoHealthIncidentTracker()

    def _generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_track_and_get_incident(self):
        repo_id = uuid.uuid4().hex
        incident_type = self._generate_random_string()
        severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        description = self._generate_random_string(20)

        incident_id = self.tracker.track_incident(repo_id, incident_type, severity, description)
        incident = self.tracker.get_incident(incident_id)

        self.assertIsNotNone(incident)
        self.assertEqual(incident['repo_id'], repo_id)
        self.assertEqual(incident['status'], 'OPEN')
        self.assertEqual(incident['severity'], severity)

    def test_ingest_anomaly_stream_valid(self):
        repo_id = uuid.uuid4().hex
        anomaly_code = self._generate_random_string()
        level = random.choice(['INFO', 'WARN', 'ERROR'])
        details = self._generate_random_string(15)

        data = {
            "repo_id": repo_id,
            "anomaly_code": anomaly_code,
            "level": level,
            "details": details
        }
        stream = io.BytesIO(json.dumps(data).encode('utf-8'))

        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertTrue(result)

        incidents = self.tracker.list_incidents_by_repo(repo_id)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]['incident_type'], anomaly_code)

    def test_resolve_incident(self):
        repo_id = uuid.uuid4().hex
        incident_id = self.tracker.track_incident(repo_id, 'TYPE', 'LOW', 'DESC')
        resolver = self._generate_random_string()
        notes = self._generate_random_string(30)

        success = self.tracker.resolve_incident(incident_id, resolver, notes)

        self.assertTrue(success)
        incident = self.tracker.get_incident(incident_id)
        self.assertEqual(incident['status'], 'RESOLVED')
        self.assertEqual(incident['resolver'], resolver)
        self.assertEqual(incident['resolution_notes'], notes)

    def test_get_incident_metrics(self):
        repo_id = uuid.uuid4().hex
        severities = ['LOW', 'HIGH', 'LOW', 'CRITICAL', 'LOW']
        for sev in severities:
            self.tracker.track_incident(repo_id, 'TYPE', sev, 'DESC')

        metrics = self.tracker.get_incident_metrics(repo_id)
        self.assertEqual(metrics['total'], 5)
        self.assertEqual(metrics['breakdown']['LOW'], 3)
        self.assertEqual(metrics['breakdown']['HIGH'], 1)

    def test_export_incident_success(self):
        repo_id = uuid.uuid4().hex
        incident_id = self.tracker.track_incident(repo_id, 'TYPE', 'LOW', 'DESC')
        endpoint = f"https://{self._generate_random_string()}.com/api"

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            result = self.tracker.export_incident(incident_id, endpoint)

            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], endpoint)
            self.assertEqual(kwargs['json']['id'], incident_id)

    def test_export_incident_request_exception(self):
        repo_id = uuid.uuid4().hex
        incident_id = self.tracker.track_incident(repo_id, 'TYPE', 'LOW', 'DESC')
        endpoint = f"https://{self._generate_random_string()}.com/api"

        with patch('requests.post', side_effect=requests.RequestException):
            result = self.tracker.export_incident(incident_id, endpoint)
            self.assertFalse(result)

    def test_ingest_anomaly_stream_invalid_data(self):
        stream = io.BytesIO(b'invalid_json_content')
        result = self.tracker.ingest_anomaly_stream(stream)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()