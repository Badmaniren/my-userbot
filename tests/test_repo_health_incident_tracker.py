import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json
from datetime import datetime

from skills.repo_health_incident_tracker import RepoHealthIncidentTracker

class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.incident_tracker = RepoHealthIncidentTracker()
        self.random_repo_id = uuid.uuid4().hex
        self.random_incident_type = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        self.random_description = f"Anomaly detected in repo {uuid.uuid4().hex}"
        self.random_payload = {
            "metric": ''.join(random.choices(string.ascii_lowercase, k=6)),
            "value": random.uniform(0.0, 100.0),
            "timestamp": datetime.utcnow().isoformat()
        }

    def test_track_incident_success(self):
        with patch('skills.repo_health_incident_tracker.uuid4', return_value=uuid.UUID(int=12345)):
            incident_id = self.incident_tracker.track_incident(
                repo_id=self.random_repo_id,
                incident_type=self.random_incident_type,
                severity=self.random_severity,
                description=self.random_description,
                metadata=self.random_payload
            )
            
            self.assertIsInstance(incident_id, str)
            self.assertTrue(len(incident_id) > 0)
            
            retrieved_incident = self.incident_tracker.get_incident(incident_id)
            self.assertEqual(retrieved_incident['repo_id'], self.random_repo_id)
            self.assertEqual(retrieved_incident['incident_type'], self.random_incident_type)
            self.assertEqual(retrieved_incident['severity'], self.random_severity)
            self.assertEqual(retrieved_incident['description'], self.random_description)
            self.assertEqual(retrieved_incident['metadata'], self.random_payload)

    def test_log_incident_anomaly_stream(self):
        stream_data = json.dumps({
            "repo_id": self.random_repo_id,
            "anomaly_code": self.random_incident_type,
            "level": self.random_severity,
            "details": self.random_description
        }).encode('utf-8')
        
        mock_file_stream = io.BytesIO(stream_data)

        with patch('skills.repo_health_incident_tracker.open', return_value=mock_file_stream, create=True):
            result = self.incident_tracker.ingest_anomaly_stream(mock_file_stream)
            self.assertTrue(result)
            
            active_incidents = self.incident_tracker.list_incidents_by_repo(self.random_repo_id)
            self.assertGreaterEqual(len(active_incidents), 1)
            found = any(inc['description'] == self.random_description for inc in active_incidents)
            self.assertTrue(found)

    def test_resolve_incident_state_transition(self):
        incident_id = self.incident_tracker.track_incident(
            repo_id=self.random_repo_id,
            incident_type=self.random_incident_type,
            severity=self.random_severity,
            description=self.random_description
        )
        
        initial_incident = self.incident_tracker.get_incident(incident_id)
        self.assertEqual(initial_incident['status'], 'OPEN')

        random_resolver = ''.join(random.choices(string.ascii_letters, k=8))
        resolution_status = self.incident_tracker.resolve_incident(
            incident_id=incident_id,
            resolver=random_resolver,
            resolution_notes=f"Fixed by {random_resolver}"
        )
        
        self.assertTrue(resolution_status)
        
        resolved_incident = self.incident_tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident['status'], 'RESOLVED')
        self.assertEqual(resolved_incident['resolver'], random_resolver)

    def test_incident_aggregation_metrics(self):
        repo_target = uuid.uuid4().hex
        severities = ['LOW', 'HIGH', 'CRITICAL', 'HIGH']
        
        for sev in severities:
            self.incident_tracker.track_incident(
                repo_id=repo_target,
                incident_type=uuid.uuid4().hex,
                severity=sev,
                description=uuid.uuid4().hex
            )
            
        metrics = self.incident_tracker.get_incident_metrics(repo_target)
        self.assertEqual(metrics['total'], 4)
        self.assertEqual(metrics['breakdown']['HIGH'], 2)
        self.assertEqual(metrics['breakdown']['CRITICAL'], 1)
        self.assertEqual(metrics['breakdown']['LOW'], 1)

    def test_export_incident_report_to_payload(self):
        incident_id = self.incident_tracker.track_incident(
            repo_id=self.random_repo_id,
            incident_type=self.random_incident_type,
            severity=self.random_severity,
            description=self.random_description
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "synced", "tracking_ref": uuid.uuid4().hex}
        
        random_endpoint = f"https://{uuid.uuid4().hex}.internal/webhook"

        with patch('skills.repo_health_incident_tracker.requests.post', return_value=mock_response) as mock_post:
            export_result = self.incident_tracker.export_incident(incident_id, random_endpoint)
            self.assertTrue(export_result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], random_endpoint)
            self.assertIn(incident_id, str(called_kwargs['json']))

if __name__ == '__main__':
    unittest.main()