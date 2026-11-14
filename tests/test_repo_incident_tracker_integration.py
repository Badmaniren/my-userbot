from datetime import datetime
import json
import os
import random
import tempfile
import unittest
import uuid

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_incident_tracker import IncidentSeverity, IncidentStatus, IncidentTracker
from skills.repo_logger import RepoLogger
from skills.vulnerability_analyzer import VulnerabilityAnalyzer


class TestRepoIncidentTrackerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.db_path = os.path.join(self.repo_path, f"incidents_{uuid.uuid4().hex}.json")

        self.logger = RepoLogger(repo_path=self.repo_path)
        self.anomaly_inspector = RepoHealthAnomalyInspector()
        self.vuln_analyzer = VulnerabilityAnalyzer(repo_path=self.repo_path)
        self.tracker = IncidentTracker(
            storage_path=self.db_path,
            repo_path=self.repo_path,
            logger=self.logger,
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_incident_tracker_lifecycle_and_persistence(self):
        unique_title = f"Crash in service {uuid.uuid4().hex[:8]}"
        unique_desc = f"Service failure detected at {datetime.now().isoformat()}"
        severity = random.choice(list(IncidentSeverity))

        incident_id = self.tracker.create_incident(
            title=unique_title,
            description=unique_desc,
            severity=severity,
        )

        self.assertIsNotNone(incident_id)
        self.assertTrue(os.path.exists(self.db_path))

        # Check initial state
        incident = self.tracker.get_incident(incident_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["status"], IncidentStatus.OPEN.value)
        self.assertEqual(incident["title"], unique_title)

        # Progress status: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED
        self.tracker.update_status(incident_id, IncidentStatus.IN_PROGRESS)
        self.assertEqual(self.tracker.get_incident(incident_id)["status"], IncidentStatus.IN_PROGRESS.value)

        self.tracker.resolve_incident(incident_id)
        self.assertEqual(self.tracker.get_incident(incident_id)["status"], IncidentStatus.RESOLVED.value)

        self.tracker.close_incident(incident_id)
        self.assertEqual(self.tracker.get_incident(incident_id)["status"], IncidentStatus.CLOSED.value)

        # Verify persistence with a new instance
        reloaded_tracker = IncidentTracker(storage_path=self.db_path)
        persisted_incident = reloaded_tracker.get_incident(incident_id)
        self.assertIsNotNone(persisted_incident)
        self.assertEqual(persisted_incident["title"], unique_title)
        self.assertEqual(persisted_incident["status"], IncidentStatus.CLOSED.value)

    def test_integration_with_anomaly_inspector(self):
        pulse_data = {
            "repo_id": f"repo_{uuid.uuid4().hex[:6]}",
            "metrics": {
                "cpu_usage": -12.5,
                "memory_leak_mb": 150.0,
            },
        }

        inspection_result = self.anomaly_inspector.inspect(
            repo_id=pulse_data["repo_id"],
            pulse_payload=pulse_data,
            threshold=100.0,
        )

        self.assertTrue(inspection_result["is_anomaly"])
        self.assertGreater(len(inspection_result["anomalies"]), 0)

        anomaly_ids = []
        for anomaly in inspection_result["anomalies"]:
            inc_id = self.tracker.record_anomaly_incident(anomaly=anomaly, severity=IncidentSeverity.HIGH)
            anomaly_ids.append(inc_id)

        self.assertEqual(len(anomaly_ids), len(inspection_result["anomalies"]))

        high_incidents = self.tracker.list_incidents(severity=IncidentSeverity.HIGH)
        self.assertEqual(len(high_incidents), len(anomaly_ids))

    def test_integration_with_vulnerability_analyzer(self):
        vuln_payload = {
            "name": f"insecure-lib-{uuid.uuid4().hex[:4]}",
            "cve": "CVE-2026-12345",
            "description": "Critical arbitrary code execution vulnerability",
        }

        inc_id = self.tracker.record_vulnerability_incident(
            vulnerability=vuln_payload,
            severity=IncidentSeverity.CRITICAL,
        )

        incident = self.tracker.get_incident(inc_id)
        self.assertIsNotNone(incident)
        self.assertEqual(incident["severity"], IncidentSeverity.CRITICAL.value)
        self.assertIn("CVE-2026-12345", incident["title"])

        self.tracker.resolve_incident(inc_id)
        resolved_incidents = self.tracker.list_incidents(status=IncidentStatus.RESOLVED)
        self.assertTrue(any(inc["id"] == inc_id for inc in resolved_incidents))


if __name__ == "__main__":
    unittest.main()
