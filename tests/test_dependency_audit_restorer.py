import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.dependency_audit_restorer import DependencyAuditRestorer


class TestDependencyAuditRestorer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.branch = f"feature/{uuid.uuid4().hex[:8]}"
        self.stream_source = f"https://registry.npmjs.org/{uuid.uuid4().hex}"
        self.output_report_name = f"report_{uuid.uuid4().hex}.json"
        self.cve_identifier = f"CVE-{random.randint(2000, 2024)}-{random.randint(10000, 99999)}"
        self.target_version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

        self.restorer = DependencyAuditRestorer(
            repo_path=self.repo_path,
            branch=self.branch,
            stream_source=self.stream_source
        )

    def test_init_sets_attributes(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        random_branch = f"release/{uuid.uuid4().hex[:6]}"
        random_stream = f"https://pypi.org/pypi/{uuid.uuid4().hex}/json"

        restorer = DependencyAuditRestorer(
            repo_path=random_path,
            branch=random_branch,
            stream_source=random_stream
        )

        self.assertEqual(restorer.repo_path, random_path)
        self.assertEqual(restorer.branch, random_branch)
        self.assertEqual(restorer.stream_source, random_stream)

    @patch("skills.dependency_audit_restorer.dependency_audit_aggregator")
    @patch("skills.dependency_audit_restorer.RepoRecovery")
    def test_audit_and_restore_success(self, mock_repo_recovery_cls, mock_aggregator):
        mock_aggregator.aggregate_dependencies.return_value = {
            "status": "SECURE",
            "vulnerabilities_found": 0,
            "report": self.output_report_name
        }

        mock_recovery_instance = mock_repo_recovery_cls.return_value
        mock_recovery_instance.recover_repository.return_value = True

        result = self.restorer.audit_and_restore(
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        self.assertTrue(result)
        mock_aggregator.aggregate_dependencies.assert_called_once_with(
            self.repo_path,
            self.output_report_name,
            self.cve_identifier,
            self.target_version
        )
        mock_recovery_instance.recover_repository.assert_not_called()

    @patch("skills.dependency_audit_restorer.dependency_audit_aggregator")
    @patch("skills.dependency_audit_restorer.RepoRecovery")
    def test_audit_and_restore_triggers_recovery_on_critical_issues(self, mock_repo_recovery_cls, mock_aggregator):
        mock_aggregator.aggregate_dependencies.return_value = {
            "status": "CRITICAL",
            "vulnerabilities_found": random.randint(1, 15),
            "cve": self.cve_identifier
        }

        mock_recovery_instance = mock_repo_recovery_cls.return_value
        mock_recovery_instance.recover_repository.return_value = True

        result = self.restorer.audit_and_restore(
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        self.assertTrue(result)
        mock_aggregator.aggregate_dependencies.assert_called_once()
        mock_recovery_instance.recover_repository.assert_called_once()

    @patch("skills.dependency_audit_restorer.dependency_audit_aggregator")
    @patch("skills.dependency_audit_restorer.RepoRecovery")
    def test_audit_and_restore_recovery_failure(self, mock_repo_recovery_cls, mock_aggregator):
        random_cve = f"CVE-{random.randint(1990, 2023)}-{random.randint(100, 9999)}"
        mock_aggregator.aggregate_dependencies.return_value = {
            "status": "CRITICAL",
            "vulnerabilities_found": random.randint(5, 50),
            "cve": random_cve
        }

        mock_recovery_instance = mock_repo_recovery_cls.return_value
        mock_recovery_instance.recover_repository.return_value = False

        result = self.restorer.audit_and_restore(
            output_report_name=self.output_report_name,
            cve_identifier=random_cve,
            target_version=self.target_version
        )

        self.assertFalse(result)
        mock_recovery_instance.recover_repository.assert_called_once()

    @patch("skills.dependency_audit_restorer.dependency_audit_aggregator")
    @patch("skills.dependency_audit_restorer.RepoRecovery")
    def test_safe_restore_stream_invocation(self, mock_repo_recovery_cls, mock_aggregator):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream_io = io.BytesIO(random_stream_data)

        mock_recovery_instance = mock_repo_recovery_cls.return_value
        mock_recovery_instance.safe_restore.return_value = True

        result = self.restorer.execute_safe_restore(stream_io)

        self.assertTrue(result)
        mock_repo_recovery_cls.assert_called_once_with(self.repo_path)
        mock_recovery_instance.safe_restore.assert_called_once_with(stream_io)

    @patch("skills.dependency_audit_restorer.dependency_audit_aggregator")
    def test_start_new_audit_stream(self, mock_aggregator):
        mock_aggregator.start_new.return_value = {
            "audit_id": uuid.uuid4().hex,
            "status": "INITIALIZED"
        }

        result = self.restorer.run_new_audit()

        self.assertIn("audit_id", result)
        self.assertEqual(result["status"], "INITIALIZED")
        mock_aggregator.start_new.assert_called_once_with(
            self.repo_path,
            self.branch,
            self.stream_source
        )


if __name__ == "__main__":
    unittest.main()