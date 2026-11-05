import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.dependency_audit_optimizer import optimize_and_apply_dependencies

class TestDependencyAuditOptimizer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.output_report = f"report_{uuid.uuid4().hex}.json"
        self.cve_id = f"CVE-{random.randint(2000, 2026)}-{random.randint(1000, 99999)}"
        self.target_version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.branch_name = f"branch-{uuid.uuid4().hex[:8]}"
        self.stream_source = f"stream-{uuid.uuid4().hex[:8]}"

    def test_optimize_and_apply_dependencies_success(self):
        random_aggregated_data = {
            "status": "success",
            "audit_id": uuid.uuid4().hex,
            "packages_checked": random.randint(5, 50)
        }
        random_pipeline_result = {
            "updated": True,
            "version": self.target_version
        }

        with patch("skills.dependency_audit_optimizer.aggregate_dependencies") as mock_aggregate, \
             patch("skills.dependency_audit_optimizer.DependencyUpdaterPipeline") as mock_pipeline_cls:
            
            mock_aggregate.return_value = random_aggregated_data
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.run.return_value = random_pipeline_result
            mock_pipeline_cls.return_value = mock_pipeline_instance

            result = optimize_and_apply_dependencies(
                repo_path=self.repo_path,
                output_report_name=self.output_report,
                cve_identifier=self.cve_id,
                target_version=self.target_version,
                branch=self.branch_name,
                stream_source=self.stream_source
            )

            mock_aggregate.assert_called_once_with(
                self.repo_path,
                self.output_report,
                self.cve_id,
                self.target_version
            )

            mock_pipeline_cls.assert_called_once_with(self.repo_path)
            mock_pipeline_instance.run.assert_called_once()

            self.assertIn("audit_result", result)
            self.assertIn("pipeline_result", result)
            self.assertEqual(result["audit_result"], random_aggregated_data)
            self.assertEqual(result["pipeline_result"], random_pipeline_result)

    def test_optimize_and_apply_dependencies_exception_handling(self):
        random_error_message = f"Error-{uuid.uuid4().hex}"

        with patch("skills.dependency_audit_optimizer.aggregate_dependencies") as mock_aggregate:
            mock_aggregate.side_effect = Exception(random_error_message)

            with self.assertRaises(Exception) as ctx:
                optimize_and_apply_dependencies(
                    repo_path=self.repo_path,
                    output_report_name=self.output_report,
                    cve_identifier=self.cve_id,
                    target_version=self.target_version,
                    branch=self.branch_name,
                    stream_source=self.stream_source
                )

            self.assertIn(random_error_message, str(ctx.exception))

if __name__ == "__main__":
    unittest.main()