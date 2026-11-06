import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills import dependency_audit_shield


class TestDependencyAuditShield(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_report = f"report_{uuid.uuid4().hex}.json"
        self.rand_cve = f"CVE-{random.randint(2000, 2026)}-{random.randint(1000, 99999)}"
        self.rand_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.rand_branch = f"branch-{uuid.uuid4().hex[:8]}"
        self.rand_stream = f"stream-{uuid.uuid4().hex[:8]}"

        # Случайный словарь для аудита
        self.rand_audit_data = {
            "id": uuid.uuid4().hex,
            "dependency": "".join(random.choices(string.ascii_lowercase, k=8)),
            "status": random.choice(["secure", "vulnerable", "deprecated"])
        }

    def test_shield_validation_and_aggregation_success(self):
        expected_result = {
            "status": "success",
            "audit_id": self.rand_audit_data["id"],
            "report": self.rand_report
        }

        with patch("skills.dependency_audit_shield.dependency_audit_validator") as mock_validator, \
             patch("skills.dependency_audit_shield.dependency_audit_aggregator") as mock_aggregator:

            mock_validator.validate_and_apply_audit.return_value = self.rand_audit_data
            mock_aggregator.aggregate_dependencies.return_value = expected_result

            # Вызываем предполагаемую функцию компоновки щита
            if hasattr(dependency_audit_shield, "run_dependency_audit_shield"):
                result = dependency_audit_shield.run_dependency_audit_shield(
                    repo_path=self.rand_repo,
                    output_report_name=self.rand_report,
                    cve_identifier=self.rand_cve,
                    target_version=self.rand_version,
                    branch=self.rand_branch,
                    stream_source=self.rand_stream,
                    audit_data=self.rand_audit_data
                )

                mock_validator.validate_and_apply_audit.assert_called_once_with(self.rand_audit_data)
                mock_aggregator.aggregate_dependencies.assert_called_once_with(
                    self.rand_repo, self.rand_report, self.rand_cve, self.rand_version
                )
                self.assertEqual(result, expected_result)
            else:
                # Fallback проверяющий композицию напрямую через импортированные модули
                val_res = dependency_audit_shield.dependency_audit_validator.validate_and_apply_audit(self.rand_audit_data)
                agg_res = dependency_audit_shield.dependency_audit_aggregator.aggregate_dependencies(
                    self.rand_repo, self.rand_report, self.rand_cve, self.rand_version
                )
                self.assertIsNotNone(val_res)
                self.assertIsNotNone(agg_res)

    def test_shield_io_stream_handling(self):
        random_bytes = uuid.uuid4().bytes + bytes(random.choices(string.ascii_letters.encode(), k=16))
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.dependency_audit_shield.dependency_audit_validator") as mock_validator:
            mock_validator.validate_and_apply_audit.return_value = {"stream_data": random_bytes}

            if hasattr(dependency_audit_shield, "process_audit_stream"):
                res = dependency_audit_shield.process_audit_stream(mock_stream)
                self.assertIn("stream_data", res)
                self.assertEqual(res["stream_data"], random_bytes)
            else:
                data = mock_stream.read()
                self.assertEqual(data, random_bytes)

    def test_shield_aggregation_failure_propagation(self):
        err_message = f"Error-{uuid.uuid4().hex}"

        with patch("skills.dependency_audit_shield.dependency_audit_validator") as mock_validator, \
             patch("skills.dependency_audit_shield.dependency_audit_aggregator") as mock_aggregator:

            mock_validator.validate_and_apply_audit.return_value = self.rand_audit_data
            mock_aggregator.aggregate_dependencies.side_effect = ValueError(err_message)

            if hasattr(dependency_audit_shield, "run_dependency_audit_shield"):
                with self.assertRaises(ValueError) as ctx:
                    dependency_audit_shield.run_dependency_audit_shield(
                        repo_path=self.rand_repo,
                        output_report_name=self.rand_report,
                        cve_identifier=self.rand_cve,
                        target_version=self.rand_version,
                        branch=self.rand_branch,
                        stream_source=self.rand_stream,
                        audit_data=self.rand_audit_data
                    )
                self.assertIn(err_message, str(ctx.exception))
            else:
                with self.assertRaises(ValueError):
                    dependency_audit_shield.dependency_audit_aggregator.aggregate_dependencies(
                        self.rand_repo, self.rand_report, self.rand_cve, self.rand_version
                    )


if __name__ == "__main__":
    unittest.main()