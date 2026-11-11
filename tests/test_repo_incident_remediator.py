import io
import os
import random
import string
import unittest
from unittest.mock import MagicMock, call, patch

from skills.repo_incident_remediator import (
    IncidentReport,
    IncidentSeverity,
    IncidentStatus,
    RemediationAction,
    RemediationValidationResult,
    RepoIncidentRemediator,
)


def _rnd_str(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _rnd_path():
    return f"/{_rnd_str(6)}/{_rnd_str(8)}/{_rnd_str(10)}"


def _rnd_bytes(length=32):
    return os.urandom(length)


class TestRepoIncidentRemediator(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = _rnd_path()
        self.random_incident_id = f"inc-{_rnd_str(10)}"
        self.random_commit_hash = _rnd_str(40)
        self.random_branch_name = f"branch-{_rnd_str(8)}"

    def test_remediator_initialization_defaults_and_customs(self):
        auto_rollback_flag = random.choice([True, False])
        mock_backup = MagicMock()
        mock_validator = MagicMock()

        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            backup_manager=mock_backup,
            validator=mock_validator,
            auto_rollback=auto_rollback_flag,
        )

        self.assertEqual(remediator.repo_path, self.random_repo_path)
        self.assertEqual(remediator.backup_manager, mock_backup)
        self.assertEqual(remediator.validator, mock_validator)
        self.assertEqual(remediator.auto_rollback, auto_rollback_flag)

    def test_diagnose_incident_integrity_corruption(self):
        remediator = RepoIncidentRemediator(repo_path=self.random_repo_path)
        rnd_err = f"fatal: loose object {_rnd_str(40)} is corrupt"
        payload = {
            "incident_id": self.random_incident_id,
            "failure_type": "git_object_corruption",
            "details": rnd_err,
            "severity": "CRITICAL",
        }

        report = remediator.diagnose_incident(payload)

        self.assertIsInstance(report, IncidentReport)
        self.assertEqual(report.incident_id, self.random_incident_id)
        self.assertEqual(report.repo_path, self.random_repo_path)
        self.assertEqual(report.failure_type, "git_object_corruption")
        self.assertEqual(report.details, rnd_err)
        self.assertEqual(report.severity, IncidentSeverity.CRITICAL)
        self.assertEqual(report.status, IncidentStatus.DIAGNOSED)

    def test_diagnose_incident_stale_lockfile(self):
        remediator = RepoIncidentRemediator(repo_path=self.random_repo_path)
        rnd_lock_path = f"{self.random_repo_path}/.git/index.lock"
        payload = {
            "incident_id": self.random_incident_id,
            "failure_type": "stale_git_lock",
            "details": f"Unable to create '{rnd_lock_path}': File exists.",
            "severity": "MEDIUM",
        }

        report = remediator.diagnose_incident(payload)

        self.assertIsInstance(report, IncidentReport)
        self.assertEqual(report.incident_id, self.random_incident_id)
        self.assertEqual(report.severity, IncidentSeverity.MEDIUM)
        self.assertIn(rnd_lock_path, report.details)

    def test_plan_remediation_creates_coherent_action(self):
        remediator = RepoIncidentRemediator(repo_path=self.random_repo_path)
        rand_details = f"Corrupt ref: refs/heads/{self.random_branch_name}"
        report = IncidentReport(
            incident_id=self.random_incident_id,
            repo_path=self.random_repo_path,
            failure_type="corrupted_ref",
            details=rand_details,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DIAGNOSED,
        )

        action = remediator.plan_remediation(report)

        self.assertIsInstance(action, RemediationAction)
        self.assertEqual(action.incident_id, self.random_incident_id)
        self.assertEqual(action.strategy, "repair_git_ref")
        self.assertIn("target_ref", action.parameters)
        self.assertIn(self.random_branch_name, action.parameters["target_ref"])
        self.assertEqual(action.status, "PLANNED")

    def test_plan_remediation_stale_lockfile_strategy(self):
        remediator = RepoIncidentRemediator(repo_path=self.random_repo_path)
        lock_file_name = f"index.lock.{_rnd_str(6)}"
        report = IncidentReport(
            incident_id=self.random_incident_id,
            repo_path=self.random_repo_path,
            failure_type="stale_git_lock",
            details=f"Remove {lock_file_name}",
            severity=IncidentSeverity.LOW,
            status=IncidentStatus.DIAGNOSED,
        )

        action = remediator.plan_remediation(report)

        self.assertIsInstance(action, RemediationAction)
        self.assertEqual(action.strategy, "remove_lockfile")
        self.assertEqual(action.incident_id, self.random_incident_id)

    def test_execute_remediation_success(self):
        remediator = RepoIncidentRemediator(repo_path=self.random_repo_path)
        rand_action_id = f"act-{_rnd_str(8)}"
        action = RemediationAction(
            action_id=rand_action_id,
            incident_id=self.random_incident_id,
            strategy="remove_lockfile",
            parameters={"lockfile_path": f"{self.random_repo_path}/.git/index.lock"},
            status="PLANNED",
        )

        with patch("skills.repo_incident_remediator.os.path.exists", return_value=True), \
             patch("skills.repo_incident_remediator.os.remove") as mock_remove:
            success = remediator.execute_remediation(action)

            self.assertTrue(success)
            self.assertEqual(action.status, "EXECUTED")
            mock_remove.assert_called_once_with(action.parameters["lockfile_path"])

    def test_execute_remediation_failure_triggers_rollback_if_enabled(self):
        mock_backup = MagicMock()
        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            backup_manager=mock_backup,
            auto_rollback=True,
        )
        rand_action_id = f"act-{_rnd_str(8)}"
        action = RemediationAction(
            action_id=rand_action_id,
            incident_id=self.random_incident_id,
            strategy="repair_git_ref",
            parameters={"target_ref": self.random_branch_name},
            status="PLANNED",
        )

        with patch.object(remediator, "_apply_strategy_repair_git_ref", side_effect=RuntimeError("Subprocess failed")), \
             patch.object(remediator, "rollback") as mock_rollback:
            success = remediator.execute_remediation(action)

            self.assertFalse(success)
            self.assertEqual(action.status, "FAILED")
            mock_rollback.assert_called_once_with(action)

    def test_execute_remediation_failure_skips_rollback_if_disabled(self):
        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            auto_rollback=False,
        )
        action = RemediationAction(
            action_id=f"act-{_rnd_str(8)}",
            incident_id=self.random_incident_id,
            strategy="repair_git_ref",
            parameters={"target_ref": self.random_branch_name},
            status="PLANNED",
        )

        with patch.object(remediator, "_apply_strategy_repair_git_ref", side_effect=Exception("Disk error")), \
             patch.object(remediator, "rollback") as mock_rollback:
            success = remediator.execute_remediation(action)

            self.assertFalse(success)
            self.assertEqual(action.status, "FAILED")
            mock_rollback.assert_not_called()

    def test_validate_remediation_pass(self):
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (True, [])
        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            validator=mock_validator,
        )
        report = IncidentReport(
            incident_id=self.random_incident_id,
            repo_path=self.random_repo_path,
            failure_type="stale_git_lock",
            details="Fixed lock",
            severity=IncidentSeverity.LOW,
            status=IncidentStatus.REMEDIATING,
        )
        action = RemediationAction(
            action_id=f"act-{_rnd_str(8)}",
            incident_id=self.random_incident_id,
            strategy="remove_lockfile",
            parameters={},
            status="EXECUTED",
        )

        result = remediator.validate_remediation(report, action)

        self.assertIsInstance(result, RemediationValidationResult)
        self.assertEqual(result.incident_id, self.random_incident_id)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_errors, [])
        mock_validator.validate.assert_called_once_with(self.random_repo_path)

    def test_validate_remediation_fail(self):
        mock_validator = MagicMock()
        rand_error_msg = f"Check failed: {_rnd_str(15)}"
        mock_validator.validate.return_value = (False, [rand_error_msg])
        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            validator=mock_validator,
        )
        report = IncidentReport(
            incident_id=self.random_incident_id,
            repo_path=self.random_repo_path,
            failure_type="git_object_corruption",
            details="Corrupted",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.REMEDIATING,
        )
        action = RemediationAction(
            action_id=f"act-{_rnd_str(8)}",
            incident_id=self.random_incident_id,
            strategy="rebuild_index",
            parameters={},
            status="EXECUTED",
        )

        result = remediator.validate_remediation(report, action)

        self.assertIsInstance(result, RemediationValidationResult)
        self.assertEqual(result.incident_id, self.random_incident_id)
        self.assertFalse(result.is_valid)
        self.assertIn(rand_error_msg, result.validation_errors)

    def test_stream_diagnostic_log_processing(self):
        remediator = RepoIncidentRemediator(repo_path=self.random_repo_path)
        rand_stream_data = _rnd_bytes(64)
        mock_stream = io.BytesIO(rand_stream_data)

        parsed_metrics = remediator.process_diagnostic_stream(mock_stream)

        self.assertIn("bytes_read", parsed_metrics)
        self.assertEqual(parsed_metrics["bytes_read"], len(rand_stream_data))
        self.assertIn("checksum", parsed_metrics)

    def test_rollback_invokes_backup_manager_restore(self):
        mock_backup = MagicMock()
        rand_snapshot_id = f"snap-{_rnd_str(12)}"
        mock_backup.create_snapshot.return_value = rand_snapshot_id

        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            backup_manager=mock_backup,
        )
        snapshot_id = remediator.create_safety_backup()
        self.assertEqual(snapshot_id, rand_snapshot_id)

        action = RemediationAction(
            action_id=f"act-{_rnd_str(8)}",
            incident_id=self.random_incident_id,
            strategy="rebuild_index",
            parameters={"snapshot_id": snapshot_id},
            status="FAILED",
        )

        rollback_res = remediator.rollback(action)
        self.assertTrue(rollback_res)
        mock_backup.restore_snapshot.assert_called_once_with(self.random_repo_path, rand_snapshot_id)

    def test_remediate_pipeline_full_success_flow(self):
        mock_backup = MagicMock()
        rand_snapshot = f"snap-{_rnd_str(10)}"
        mock_backup.create_snapshot.return_value = rand_snapshot

        mock_validator = MagicMock()
        mock_validator.validate.return_value = (True, [])

        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            backup_manager=mock_backup,
            validator=mock_validator,
            auto_rollback=True,
        )

        incident_payload = {
            "incident_id": self.random_incident_id,
            "failure_type": "stale_git_lock",
            "details": f"Lock exists at {self.random_repo_path}/.git/index.lock",
            "severity": "MEDIUM",
        }

        with patch.object(remediator, "execute_remediation", return_value=True) as mock_exec:
            res = remediator.remediate_pipeline(incident_payload)

            self.assertEqual(res["status"], IncidentStatus.RESOLVED.value)
            self.assertEqual(res["incident_id"], self.random_incident_id)
            self.assertTrue(res["validated"])
            self.assertEqual(res["backup_id"], rand_snapshot)
            mock_exec.assert_called_once()
            mock_validator.validate.assert_called_once_with(self.random_repo_path)

    def test_remediate_pipeline_validation_failed_triggers_rollback(self):
        mock_backup = MagicMock()
        rand_snapshot = f"snap-{_rnd_str(10)}"
        mock_backup.create_snapshot.return_value = rand_snapshot

        mock_validator = MagicMock()
        mock_fail_reason = f"Ref check failed: {_rnd_str(12)}"
        mock_validator.validate.return_value = (False, [mock_fail_reason])

        remediator = RepoIncidentRemediator(
            repo_path=self.random_repo_path,
            backup_manager=mock_backup,
            validator=mock_validator,
            auto_rollback=True,
        )

        incident_payload = {
            "incident_id": self.random_incident_id,
            "failure_type": "corrupted_ref",
            "details": f"Corrupt head {_rnd_str(40)}",
            "severity": "HIGH",
        }

        with patch.object(remediator, "execute_remediation", return_value=True), \
             patch.object(remediator, "rollback") as mock_rollback:
            res = remediator.remediate_pipeline(incident_payload)

            self.assertEqual(res["status"], IncidentStatus.FAILED.value)
            self.assertEqual(res["incident_id"], self.random_incident_id)
            self.assertFalse(res["validated"])
            self.assertIn(mock_fail_reason, res["errors"])
            mock_rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()