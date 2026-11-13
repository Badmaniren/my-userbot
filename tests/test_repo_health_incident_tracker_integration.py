import unittest
import uuid
import random
import io
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker, track_incident

class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def test_end_to_end_incident_lifecycle_and_ingestion(self):
        tracker = RepoHealthIncidentTracker()
        
        # Генерация случайных входных данных для исключения хардкода
        rand_suffix = str(uuid.uuid4())[:8]
        repo_id = f"repo-{rand_suffix}"
        anomaly_code = f"ERR_CODE_{rand_suffix}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        description = f"Automated test anomaly description {rand_suffix}"
        
        # 1. Проверка прямого трекинга через инстанс
        incident_id = tracker.track_incident(
            repo_id=repo_id,
            incident_type=anomaly_code,
            severity=severity,
            description=description,
            metadata={"env": "integration-test"}
        )
        
        self.assertIsNotNone(incident_id)
        
        # 2. Проверка получения инцидента
        incident = tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["repo_id"], repo_id)
        self.assertEqual(incident["incident_type"], anomaly_code)
        self.assertEqual(incident["severity"], severity)
        self.assertEqual(incident["description"], description)
        self.assertEqual(incident["status"], "OPEN")
        
        # 3. Проверка ингеста потока (anomaly stream) без моков
        stream_rand_suffix = str(uuid.uuid4())[:8]
        stream_repo_id = f"stream-repo-{stream_rand_suffix}"
        stream_payload = {
            "repo_id": stream_repo_id,
            "anomaly_code": f"STREAM_ERR_{stream_rand_suffix}",
            "level": "CRITICAL",
            "details": "Stream injected anomaly details"
        }
        stream_data = io.BytesIO(str(stream_payload).replace("'", '"').encode("utf-8"))
        
        ingest_result = tracker.ingest_anomaly_stream(stream_data)
        self.assertTrue(ingest_result)
        
        stream_incidents = tracker.list_incidents_by_repo(stream_repo_id)
        self.assertEqual(len(stream_incidents), 1)
        self.assertEqual(stream_incidents[0]["incident_type"], stream_payload["anomaly_code"])
        
        # 4. Проверка разрешения инцидента
        resolver_name = f"admin-{rand_suffix}"
        resolution_notes = "Fixed via integration test runner"
        resolve_result = tracker.resolve_incident(incident_id, resolver_name, resolution_notes)
        self.assertTrue(resolve_result)
        
        resolved_incident = tracker.get_incident(incident_id)
        self.assertEqual(resolved_incident["status"], "RESOLVED")
        self.assertEqual(resolved_incident["resolver"], resolver_name)
        self.assertEqual(resolved_incident["resolution_notes"], resolution_notes)
        
        # 5. Проверка метрик
        metrics = tracker.get_metrics() if hasattr(tracker, "get_metrics") else tracker.get_incident_metrics(repo_id)
        self.assertIsInstance(metrics, dict)
        self.assert