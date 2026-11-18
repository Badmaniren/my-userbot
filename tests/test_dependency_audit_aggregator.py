import os
import json
import logging
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.dependency_audit_aggregator import start_new, aggregate_dependencies


class TestDependencyAuditAggregator(unittest.TestCase):

    def setUp(self):
        self.repo_path_rand = f"/tmp/{uuid.uuid4().hex}"
        self.branch_rand = f"feature-{uuid.uuid4().hex[:6]}"
        self.stream_content = uuid.uuid4().bytes

    def test_start_new_clean_stream(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        stream_io = io.BytesIO(self.stream_content)

        with patch('skills.vulnerability_analyzer.scan_from_stream', create=True) as mock_scan_stream, \
             patch('skills.repo_reporter.generate_clean_report', create=True) as mock_clean_report:

            mock_scan_stream.return_value = {"vulnerabilities": []}
            mock_clean_report.return_value = {rand_key: rand_val}

            res = start_new(repo_path=self.repo_path_rand, branch=self.branch_rand, stream_source=stream_io)
            
            mock_scan_stream.assert_called_once_with(stream_io)
            mock_clean_report.assert_called_once()
            self.assertEqual(res.get(rand_key), rand_val)

    def test_start_new_clean_repo_path(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        with patch('skills.vulnerability_analyzer.scan_vulnerabilities', create=True) as mock_scan_vuln, \
             patch('skills.repo_reporter.generate_clean_report', create=True) as mock_clean_report:
            
            mock_scan_vuln.return_value = {"vulnerabilities": []}
            mock_clean_report.return_value = {rand_key: rand_val}

            res = start_new(repo_path=self.repo_path_rand, branch=self.branch_rand)

            mock_scan_vuln.assert_called_once_with(self.repo_path_rand)
            mock_clean_report.assert_called_once()
            self.assertEqual(res.get(rand_key), rand_val)

    def test_start_new_with_vulnerabilities(self):
        pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        cve_id = f"CVE-2023-{random.randint(1000, 9999)}"
        vuln_data = {"vulnerabilities": [{"package": pkg_name, "cve": cve_id}]}
        
        update_ret_key = uuid.uuid4().hex
        update_ret_val = uuid.uuid4().hex
        agg_ret_key = uuid.uuid4().hex
        agg_ret_val = uuid.uuid4().hex

        with patch('skills.vulnerability_analyzer.scan_vulnerabilities', create=True) as mock_scan_vuln, \
             patch('skills.dependency_updater_pipeline.run_update', create=True) as mock_run_update, \
             patch('skills.repo_reporter.generate_aggregate_report', create=True) as mock_agg_report:
            
            mock_scan_vuln.return_value = vuln_data
            mock_run_update.return_value = {update_ret_key: update_ret_val}
            mock_agg_report.return_value = {agg_ret_key: agg_ret_val}

            res = start_new(repo_path=self.repo_path_rand, branch=self.branch_rand)

            mock_scan_vuln.assert_called_once_with(self.repo_path_rand)
            mock_run_update.assert_called_once_with(self.repo_path_rand, self.branch_rand)
            mock_agg_report.assert_called_once_with(vuln_data, {update_ret_key: update_ret_val})
            self.assertEqual(res.get(agg_ret_key), agg_ret_val)

    def test_start_new_exception_logging(self):
        err_msg = uuid.uuid4().hex

        with patch('skills.vulnerability_analyzer.scan_vulnerabilities', side_effect=Exception(err_msg), create=True) as mock_scan_vuln, \
             patch('logging.Logger.error') as mock_log_error:

            with self.assertRaises(Exception) as ctx:
                start_new(repo_path=self.repo_path_rand, branch=self.branch_rand)
            
            self.assertIn(err_msg, str(ctx.exception))
            mock_log_error.assert_called_once()

    def test_aggregate_dependencies_writes_file(self):
        pkg_rand = f"lib-{uuid.uuid4().hex[:5]}"
        cve_rand = f"CVE-2024-{random.randint(10000, 99999)}"
        version_rand = f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}"
        report_name = f"report-{uuid.uuid4().hex[:6]}.json"

        os.makedirs(self.repo_path_rand, exist_ok=True)
        req_file_path = os.path.join(self.repo_path_rand, "requirements.txt")

        with open(req_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Comment line\n{pkg_rand}=={version_rand}\n")

        try:
            result = aggregate_dependencies(
                repo_path=self.repo_path_rand,
                output_report_name=report_name,
                cve_identifier=cve_rand,
                target_version=version_rand
            )

            self.assertEqual(result["status"], "SUCCESS")
            expected_report_path = os.path.join(self.repo_path_rand, report_name)
            self.assertEqual(result["report_path"], expected_report_path)

            self.assertTrue(os.path.exists(expected_report_path))
            with open(expected_report_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["package"], pkg_rand)
            self.assertEqual(data["cve"], cve_rand)
            self.assertEqual(data["target_version"], version_rand)
            self.assertEqual(data["status"], "AGGREGATED")

        finally:
            if os.path.exists(req_file_path):
                os.remove(req_file_path)
            report_full_path = os.path.join(self.repo_path_rand, report_name)
            if os.path.exists(report_full_path):
                os.remove(report_full_path)
            if os.path.exists(self.repo_path_rand):
                try:
                    os.rmdir(self.repo_path_rand)
                except OSError:
                    pass


if __name__ == '__main__':
    unittest.main()