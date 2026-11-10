import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_incident_lifecycle_and_anomaly_stream_integration(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        anomaly_code = f"ERR_CODE_{random.randint(1000, 9999)}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"Integration test anomaly details {uuid.uuid4()}"
        
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=anomaly_code,
            severity=severity,
            description=details,
            metadata={"source": "integration_test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        fetched = tracker.get_incident(incident_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched['repo_id'], repo_id)
        self.assertEqual(fetched['incident_type'], anomaly_code)
        self.assertEqual(fetched['severity'], severity)
        self.assertEqual(fetched['description'], details)
        self.assertEqual(fetched['status'], 'OPEN')
        
        resolver = f"user-{uuid.uuid4()}"
        resolution_notes = f"Resolved via integration test {uuid.uuid4()}"
        resolved = tracker.resolve_incident(incident_id, resolver, resolution_notes)
        self.assertTrue(resolved)
        
        fetched_resolved = tracker.get_incident(incident_id)
        self.assertEqual(fetched_resolved['status'], 'RESOLVED')
        self.assertEqual(fetched_resolved['resolver'], resolver)
        self.assertEqual(fetched_resolved['resolution_notes'], resolution_notes)
        
        metrics = tracker.get_incident_metrics(repo_id)
        self.assertEqual(metrics['total'], 1)
        self.assertEqual(metrics['breakdown'].get(severity), 1)
        
        stream_repo_id = f"repo-stream-{uuid.uuid4()}"
        stream_code = f"STREAM_ERR_{random.randint(100, 999)}"
        stream_level = "HIGH"
        stream_details = f"Stream ingestion test {uuid.uuid4()}"
        
        payload = f'{{"repo_id": "{stream_repo_id}", "anomaly_code": "{stream_code}", "level": "{stream_level}", "details": "{stream_details}"}}'
        file_stream = io.BytesIO(payload.encode('utf-8'))
        
        ingested = tracker.ingest_anomaly_stream(file_stream)
        self.assertTrue(ingested)
        
        stream_incidents = tracker.list_incidents_by_repo(stream_repo_id)
        self.assertEqual(len(stream_incidents), 1)
        self.assertEqual(stream_incidents[0]['incident_type'], stream_code)
        self.assertEqual(stream_incidents[0]['severity'], stream_level)
        self.assertEqual(stream_incidents[0]['description'], stream_details)

    def test_global_track_incident_wrapper(self):
        repo_id = f"repo-wrapper-{uuid.uuid4()}"
        anomaly_code = f"WRAPPER_ERR_{random.randint(10, 99)}"
        severity = "LOW"
        description = f"Wrapper test {uuid.uuid4()}"
        
        incident_id = track_incident(
            repo_id=repo_id,
            incident_type=anomaly_code,
            severity=severity,
            description=description
        )
        
        self.assertIsNotNone(incident_id)
        self.assertIsInstance(str(incident_id), str)

if __name__ == '__main__':
    unittest.main()