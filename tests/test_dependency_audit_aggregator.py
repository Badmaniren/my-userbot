import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import sys
import types
import io

mock_modules = [
    'vulnerability_analyzer',
    'dependency_updater_pipeline',
    'repo_reporter'
]
for mod_name in mock_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

from skills.dependency_audit_aggregator import start_new, aggregate_dependencies

class TestDependencyAuditAggregator(unittest.TestCase):

    def test_start_new_clean_report_default(self):
        rand_repo = uuid.uuid4().hex
        rand_branch = uuid.uuid4().hex
        with patch('vulnerability_analyzer.scan_vulnerabilities', return_value={"vulnerabilities": []}, create=True) as mock_scan, \
             patch('repo_reporter.generate_clean_report', return_value={"secure": True, "message": uuid.uuid4().hex}, create=True) as mock_clean:
            
            res = start_new(repo_path=rand_repo, branch=rand_branch)
            mock_scan.assert_called_once_with(rand_repo)
            mock_clean.assert_called_once()
            self.assertIn("secure", res)

    def test_start_new_stream_source(self):
        rand_stream = io.BytesIO(uuid.uuid4().bytes)
        rand_vuln_id = uuid.uuid4().hex
        vuln_dict = {"vulnerabilities": [{"id": rand_vuln_id}]}
        update_dict = {"updated": uuid.uuid4().hex}
        aggregate_dict = {"status": uuid.uuid4().hex, "vulns": vuln_dict, "updates": update_dict}

        with patch('vulnerability_analyzer.scan_from_stream', return_value=vuln_dict, create=True) as mock_stream_scan, \
             patch('dependency_updater_pipeline.run_update', return_value=update_dict, create=True) as mock_update, \
             patch('repo_reporter.generate_aggregate_report', return_value=aggregate_dict, create=True) as mock_agg:
            
            res = start_new(stream_source=rand_stream)
            mock_stream_scan.assert_called_once_with(rand_stream)
            mock_update.assert_called()
            mock_agg.assert_called_once_with(vuln_dict, update_dict)
            self.assertEqual(res, aggregate_dict)

    def test_start_new_exception_logging(self):
        rand_repo = uuid.uuid4().hex
        rand_err_msg = uuid.uuid4().hex
        
        with patch('vulnerability_analyzer.scan_vulnerabilities', side_effect=Exception(rand_err_msg), create=True), \
             patch('skills.dependency_audit_aggregator.logging') as mock_logging:
            
            mock_logger = MagicMock()
            mock_logging.getLogger.return_value = mock_logger

            with self.assertRaises(Exception) as ctx:
                start_new(repo_path=rand_repo)
            
            self.assertEqual(str(ctx.exception), rand_err_msg)
            mock_logger.error.assert_called_once_with(rand_err_msg)

    def test_aggregate_dependencies_integration(self):
        rand_dir = uuid.uuid4().hex
        rand_pkg = uuid.uuid4().hex
        rand_ver = str(random.randint(1, 9)) + "." + str(random.randint(0, 9))
        rand_cve = "CVE-" + str(random.randint(1000, 9999)) + "-" + str(random.randint(10000, 99999))
        rand_report_name = uuid.uuid4().hex + ".json"

        req_content = f"{rand_pkg}=={rand_ver}\n"

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open(read_data=req_content)) as mock_file, \
             patch('os.path.join', side_effect=lambda *args: "/".join(args)), \
             patch('json.dump') as mock_json_dump:

            res = aggregate_dependencies(
                repo_path=rand_dir,
                output_report_name=rand_report_name,
                cve_identifier=rand_cve,
                target_version=rand_ver
            )

            self.assertEqual(res["status"], "SUCCESS")
            self.assertIn(rand_report_name, res["report_path"])
            mock_json_dump.assert_called_once()
            dumped_data = mock_json_dump.call_args[0][0]
            self.assertEqual(dumped_data["package"], rand_pkg)
            self.assertEqual(dumped_data["cve"], rand_cve)
            self.assertEqual(dumped_data["target_version"], rand_ver)
            self.assertEqual(dumped_data["status"], "AGGREGATED")