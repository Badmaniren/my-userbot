import unittest
import uuid
import random
import json
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_full_incident_lifecycle_and_aggregation(self):
        tracker = RepoHealthIncidentTracker()
        
        repo_id = f"repo-{uuid.uuid4()}"
        anomaly_types = ["CRITICAL_VULN", "MEMORY_LEAK", "BUILD_FAILURE", "DEPRECATED_DEPENDENCY"]
        severities = ["HIGH", "CRITICAL", "MEDIUM", "LOW"]
        
        created_ids = []
        for _ in range(random.randint(3, 6)):
            inc_type = random.choice(anomaly_types)
            sev = random.choice(severities)
            desc = f"Automated anomaly detected with code {uuid.uuid4()}"
            metadata = {"source": "integration_test", "retry_count": random.randint(0, 3)}
            
            incident_id = tracker.track_incident(
                repo_id=repo_id,
                incident_type=inc_type,
                severity=sev,
                description=desc,
                metadata=metadata
            )
            self.assertIsNotNone(incident_id)
            created_ids.append(incident_id)
            
            fetched = tracker.get_incident(incident_id)
            self.assertEqual(fetched["repo_id"], repo_id)
            self.assertEqual(fetched["status"], "OPEN")
            self.assertEqual(fetched["metadata"]["retry_count"], metadata["retry_count"])

        payload = {
            "repo_id": repo_id,
            "anomaly_code": random.choice(anomaly_types),
            "level": random.choice(severities),
            "details": f"Stream anomaly {uuid.uuid4()}"
        }
        stream_data = json.dumps(payload).encode("utf-8")
        stream_mock = io.BytesIO(stream_data)
        
        ingest_result = tracker.ingest_anomaly_stream(stream_mock)
        self.assertTrue(ingest_result)

        incidents_list = tracker.list_incidents_by_repo(repo_id)
        self.assertEqual(len(incidents_list), len(created_ids) + 1)

        target_incident_id = created_ids[0]
        resolver_name = f"AutoRemediator-{uuid.uuid4()}"
        resolution_notes = f"Fixed automatically via pipeline run {uuid.uuid4()}"
        
        resolve_success = tracker.resolve_incident(target_incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_success)
        
        resolved_incident = tracker.get_incident(target_incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)

        metrics = tracker.get_incident_metrics(repo_id)
        self.assertEqual(metrics["total"], len(created_ids) + 1)
        self.assertIsInstance(metrics["breakdown"], dict)
        self.assertGreaterEqual(sum(metrics["breakdown"].values()), metrics["total"])

        global_id = track_incident(
            repo_id=repo_id,
            incident_type="GLOBAL_TEST_ANOMALY",
            severity="LOW",
            description=str(uuid.uuid4())
        )
        self.assertIsNotNone(global_id)

if __name__ == "__main__":
    unittest.main()