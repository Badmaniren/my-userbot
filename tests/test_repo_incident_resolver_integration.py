import unittest
import uuid
import tempfile
import shutil
from pathlib import Path

from skills.repo_incident_resolver import RepoIncidentResolver
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker
from skills.repo_health_restorer import RepoHealthRestorer


class IntegrationTestRepoIncidentResolver(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)

        self.tracker = RepoHealthIncidentTracker()
        self.resolver_module = RepoIncidentResolver(
            repo_path=str(self.repo_path),
            tracker=self.tracker
        )

        self.repo_id = f"repo-{uuid.uuid4()}"
        self.incident_type = "CORRUPTED_INDEX"
        self.severity = "HIGH"
        self.description = f"Test incident description {uuid.uuid4()}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_incident_resolution_flow(self):
        tracking_result = self.tracker.track_incident(
            repo_id=self.repo_id,
            incident_type=self.incident_type,
            severity=self.severity,
            description=self.description,
            metadata={"random_seed": str(uuid.uuid4())}
        )

        if isinstance(tracking_result, dict):
            incident_id = tracking_result.get("incident_id") or tracking_result.get("id")
        else:
            incident_id = str(tracking_result)
        self.assertIsNotNone(incident_id, "Tracker must return an incident ID")

        incident_data = self.tracker.get_incident(incident_id)
        self.assertEqual(incident_data.get("status"), "OPEN")

        resolver_name = f"user-{uuid.uuid4()}"
        resolution_notes = f"Fixed by automated integration test {uuid.uuid4()}"

        resolution_result = self.resolver_module.resolve_incident(
            incident_id=incident_id,
            repo_path=str(self.repo_path),
            resolver=resolver_name,
            resolution_notes=resolution_notes
        )

        self.assertTrue(
            resolution_result.get("success"),
            f"Resolution failed with error: {resolution_result.get('error')}"
        )
        self.assertEqual(resolution_result.get("incident_id"), incident_id)
        self.assertIn("restoration_metrics", resolution_result)

        updated_incident = self.tracker.get_incident(incident_id)
        self.assertEqual(updated_incident.get("status"), "RESOLVED")
        self.assertEqual(updated_incident.get("resolver"), resolver_name)
        self.assertEqual(updated_incident.get("resolution_notes"), resolution_notes)

    def test_batch_resolve_repo_incidents(self):
        inc1 = self.tracker.track_incident(self.repo_id, "ERR_1", "MED", "Desc 1", {})
        inc2 = self.tracker.track_incident(self.repo_id, "ERR_2", "HIGH", "Desc 2", {})

        id1 = inc1.get("incident_id") or inc1.get("id") if isinstance(inc1, dict) else str(inc1)
        id2 = inc2.get("incident_id") or inc2.get("id") if isinstance(inc2, dict) else str(inc2)

        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)

        resolver_name = f"admin-{uuid.uuid4()}"
        notes = f"Batch resolution notes {uuid.uuid4()}"

        summary = self.resolver_module.resolve_repo_incidents(
            repo_id=self.repo_id,
            repo_path=str(self.repo_path),
            resolver=resolver_name,
            resolution_notes=notes
        )

        self.assertGreaterEqual(summary.get("total_resolved"), 2)
        resolved_list = summary.get("resolved_incidents", [])
        self.assertIn(id1, resolved_list)
        self.assertIn(id2, resolved_list)

        all_resolved = self.resolver_module.resolve_all_for_repo(
            repo_id=self.repo_id,
            repo_path=str(self.repo_path)
        )
        self.assertIsInstance(all_resolved, list)


if __name__ == "__main__":
    unittest.main()