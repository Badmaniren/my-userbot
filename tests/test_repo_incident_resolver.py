import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.repo_incident_resolver import RepoIncidentResolver
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker
from skills.repo_health_restorer import RepoHealthRestorer


class TestRepoIncidentResolver(unittest.TestCase):
    def setUp(self):
        self.rand_repo_path = f"/var/repos/{uuid.uuid4().hex[:6]}/{uuid.uuid4().hex[:8]}"
        self.rand_repo_id = f"repo-{uuid.uuid4().hex[:8]}"
        self.rand_incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        self.rand_resolver = f"admin-{uuid.uuid4().hex[:6]}"
        self.rand_notes = f"Fixed via automated routine {uuid.uuid4().hex[:6]}"

        self.mock_tracker = MagicMock(spec=RepoHealthIncidentTracker)
        self.resolver = RepoIncidentResolver(
            repo_path=self.rand_repo_path,
            tracker=self.mock_tracker
        )

    def test_get_restorer_default(self):
        res = self.resolver._get_restorer(self.rand_repo_path)
        self.assertIsInstance(res, RepoHealthRestorer)

    def test_get_restorer_with_factory(self):
        custom_restorer = MagicMock()
        resolver_custom = RepoIncidentResolver(
            repo_path=self.rand_repo_path,
            tracker=self.mock_tracker,
            restorer=custom_restorer
        )
        self.assertEqual(resolver_custom._get_restorer(self.rand_repo_path), custom_restorer)

    def test_resolve_single_incident_success(self):
        metrics_key = uuid.uuid4().hex
        metrics_val = random.randint(100, 999)
        mock_restorer_instance = MagicMock()
        mock_restorer_instance.execute_restoration_routine.return_value = True
        mock_restorer_instance.restore_and_protect.return_value = {metrics_key: metrics_val}

        tracker_response = {"status": "RESOLVED", "id": self.rand_incident_id}
        self.mock_tracker.resolve_incident.return_value = tracker_response

        with patch("skills.repo_incident_resolver.RepoHealthRestorer", return_value=mock_restorer_instance) as mock_restorer_cls:
            result = self.resolver.resolve_incident(
                incident_id=self.rand_incident_id,
                resolver=self.rand_resolver,
                resolution_notes=self.rand_notes
            )

            mock_restorer_cls.assert_called_once_with(repo_path=self.rand_repo_path)
            mock_restorer_instance.execute_restoration_routine.assert_called_once()
            self.mock_tracker.resolve_incident.assert_called_once_with(
                incident_id=self.rand_incident_id,
                resolver=self.rand_resolver,
                resolution_notes=self.rand_notes
            )

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("incident_id"), self.rand_incident_id)
            self.assertEqual(result.get("restoration_metrics"), {metrics_key: metrics_val})
            self.assertEqual(result.get("tracker_result"), tracker_response)

    def test_resolve_incident_routine_fails_fallback(self):
        mock_restorer_instance = MagicMock()
        mock_restorer_instance.execute_restoration_routine.return_value = False
        mock_restorer_instance.restore_and_protect.return_value = {}

        with patch("skills.repo_incident_resolver.RepoHealthRestorer", return_value=mock_restorer_instance):
            result = self.resolver.resolve_incident(
                incident_id=self.rand_incident_id
            )

            mock_restorer_instance.execute_restoration_routine.assert_called_once()
            mock_restorer_instance.restore_and_protect.assert_called_once()
            self.assertFalse(result.get("success"))
            self.assertEqual(result.get("incident_id"), self.rand_incident_id)
            self.assertEqual(result.get("error"), "Restoration routine failed")

    def test_resolve_incident_with_anomaly_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        restore_payload = {uuid.uuid4().hex: random.choice([True, False])}
        tracker_payload = {"status": "RESOLVED", "note": uuid.uuid4().hex}

        mock_restorer_instance = MagicMock()
        mock_restorer_instance.comprehensive_health_restoration.return_value = restore_payload
        self.mock_tracker.resolve_incident.return_value = tracker_payload

        with patch("skills.repo_incident_resolver.RepoHealthRestorer", return_value=mock_restorer_instance) as mock_restorer_cls:
            result = self.resolver.resolve_with_stream(
                incident_id=self.rand_incident_id,
                stream=stream_data,
                resolver=self.rand_resolver,
                resolution_notes=self.rand_notes
            )

            mock_restorer_cls.assert_called_once_with(repo_path=self.rand_repo_path)
            mock_restorer_instance.comprehensive_health_restoration.assert_called_once_with(stream_data)
            self.mock_tracker.resolve_incident.assert_called_once_with(
                incident_id=self.rand_incident_id,
                resolver=self.rand_resolver,
                resolution_notes=self.rand_notes
            )

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("restoration_result"), restore_payload)
            self.assertEqual(result.get("tracker_result"), tracker_payload)

    def test_resolve_repo_incidents_empty(self):
        self.mock_tracker.list_incidents_by_repo.return_value = []

        summary = self.resolver.resolve_repo_incidents(repo_id=self.rand_repo_id)
        self.assertEqual(summary.get("total_resolved"), 0)
        self.assertEqual(summary.get("resolved_incidents"), [])

    def test_resolve_repo_incidents_batch(self):
        inc_id_1 = f"inc-{uuid.uuid4().hex[:6]}"
        inc_id_2 = f"inc-{uuid.uuid4().hex[:6]}"
        inc_list = [
            {"id": inc_id_1, "status": "OPEN"},
            {"incident_id": inc_id_2, "status": "PENDING"},
            {"id": f"inc-{uuid.uuid4().hex[:6]}", "status": "RESOLVED"}
        ]
        self.mock_tracker.list_incidents_by_repo.return_value = inc_list

        mock_restorer_instance = MagicMock()
        mock_restorer_instance.execute_restoration_routine.return_value = True
        mock_restorer_instance.restore_and_protect.return_value = {}

        self.mock_tracker.resolve_incident.return_value = {"status": "OK"}

        with patch("skills.repo_incident_resolver.RepoHealthRestorer", return_value=mock_restorer_instance):
            summary = self.resolver.resolve_repo_incidents(
                repo_id=self.rand_repo_id,
                resolver=self.rand_resolver
            )

            self.assertEqual(summary.get("total_resolved"), 2)
            self.assertIn(inc_id_1, summary.get("resolved_incidents"))
            self.assertIn(inc_id_2, summary.get("resolved_incidents"))

    def test_resolve_all_for_repo_wrapper(self):
        inc_id = f"inc-{uuid.uuid4().hex[:6]}"
        inc_list = [{"id": inc_id, "status": "INVESTIGATING"}]
        self.mock_tracker.list_incidents_by_repo.return_value = inc_list

        mock_restorer_instance = MagicMock()
        mock_restorer_instance.execute_restoration_routine.return_value = True
        mock_restorer_instance.restore_and_protect.return_value = {}
        self.mock_tracker.resolve_incident.return_value = {"status": "OK"}

        with patch("skills.repo_incident_resolver.RepoHealthRestorer", return_value=mock_restorer_instance):
            all_resolved = self.resolver.resolve_all_for_repo(repo_id=self.rand_repo_id)
            self.assertEqual(all_resolved, [inc_id])

    def test_resolve_incident_exception_handling(self):
        mock_restorer_instance = MagicMock()
        mock_restorer_instance.execute_restoration_routine.side_effect = RuntimeError("Fatal hardware failure")

        with patch("skills.repo_incident_resolver.RepoHealthRestorer", return_value=mock_restorer_instance):
            result = self.resolver.resolve_incident(incident_id=self.rand_incident_id)
            self.assertFalse(result.get("success"))
            self.assertEqual(result.get("incident_id"), self.rand_incident_id)
            self.assertIn("Fatal hardware failure", result.get("error"))