import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.repo_health_diagnostic import RepoHealthDiagnostic

class TestRepoHealthDiagnostic(unittest.TestCase):

    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_threshold = random.randint(10, 1000)

    def test_run_full_diagnostic_success(self):
        sub_modules = [
            'changelog_generator', 'dependency_audit_aggregator', 'repo_auditor', 
            'vulnerability_analyzer', 'repo_ci_pipeline', 'repo_security_gateway'
        ]
        selected_mod = random.choice(sub_modules)
        expected_output_val = uuid.uuid4().hex

        with patch('skills.repo_health_diagnostic.RepoHealthDiagnostic._execute_sub_module') as mock_exec:
            mock_exec.return_value = {self.random_metric_name: expected_output_val}
            
            result = self.diagnostic.run_full_diagnostic(self.random_repo_path)
            
            self.assertIsInstance(result, dict)
            mock_exec.assert_called()
            self.assertIn(self.random_metric_name, result.get(selected_mod, {}))
            self.assertEqual(result[selected_mod][self.random_metric_name], expected_output_val)

    def test_analyze_codebase_structure_no_mocks_io(self):
        random_file_content = ''.join(random.choices(string.ascii_letters + string.whitespace, k=50))
        fake_stream = io.BytesIO(random_file_content.encode('utf-8'))

        with patch('os.walk') as mock_walk, \
             patch('builtins.open', return_value=fake_stream) as mock_open:
            
            mock_walk.return_value = [
                (self.random_repo_path, ('src',), (f"{uuid.uuid4().hex}.py",))
            ]

            metrics = self.diagnostic.analyze_codebase_structure(self.random_repo_path)
            
            self.assertIsInstance(metrics, dict)
            self.assertGreaterEqual(metrics.get('file_count', 0), 1)

    def test_dependency_health_check_failure_simulation(self):
        err_message = f"Dependency error: {uuid.uuid4().hex}"
        
        with patch('skills.repo_health_diagnostic.RepoHealthDiagnostic._audit_dependencies', side_effect=Exception(err_message)) as mock_audit:
            with self.assertRaises(Exception) as ctx:
                self.diagnostic.perform_deep_health_check(self.random_repo_path, self.random_threshold)
            
            self.assertIn(err_message, str(ctx.exception))
            mock_audit.assert_called_once_with(self.random_repo_path)

    def test_evaluate_health_thresholds(self):
        metric_key = uuid.uuid4().hex
        high_val = self.random_threshold + random.randint(1, 500)
        low_val = max(0, self.random_threshold - random.randint(1, 10))

        diagnostic_data = {
            metric_key: high_val
        }

        status_high = self.diagnostic.evaluate_threshold(diagnostic_data, metric_key, self.random_threshold)
        self.assertFalse(status_high)

        diagnostic_data_low = {
            metric_key: low_val
        }
        status_low = self.diagnostic.evaluate_threshold(diagnostic_data_low, metric_key, self.random_threshold)
        self.assertTrue(status_low)

    def test_generate_diagnostic_report_stream(self):
        report_id = uuid.uuid4().hex
        mock_data = {
            "diagnostic_id": report_id,
            "status": random.choice(["HEALTHY", "CRITICAL", "WARNING"]),
            "score": random.uniform(0.0, 100.0)
        }

        with patch('skills.repo_health_diagnostic.RepoHealthDiagnostic.run_full_diagnostic', return_value=mock_data):
            report_stream = self.diagnostic.export_report_stream(self.random_repo_path)
            
            self.assertIsInstance(report_stream, io.StringIO)
            content = report_stream.read()
            self.assertIn(report_id, content)

if __name__ == '__main__':
    unittest.main()