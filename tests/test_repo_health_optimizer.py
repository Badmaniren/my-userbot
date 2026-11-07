import unittest
from unittest.mock import patch, MagicMock
import os
import io
import random
import uuid
import string

from skills.repo_health_optimizer import RepoHealthOptimizer


class TestRepoHealthOptimizer(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.optimizer = RepoHealthOptimizer(self.random_repo_path)

    def test_init_sets_attributes(self):
        self.assertEqual(self.optimizer.repo_path, self.random_repo_path)
        self.assertIsNotNone(self.optimizer.restorer)
        self.assertIsNotNone(self.optimizer.vulnerability_analyzer)

    @patch('skills.repo_health_optimizer.os.makedirs')
    def test_optimize_repository_success(self, mock_makedirs):
        expected_restoration = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_vulnerability = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.optimizer.restorer, 'restore_and_protect', return_value=expected_restoration) as mock_restore, \
             patch.object(self.optimizer.vulnerability_analyzer, 'run', return_value=expected_vulnerability) as mock_vuln:
            
            self.optimizer.vulnerability_analyzer.report_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
            
            result = self.optimizer.optimize_repository()

            mock_restore.assert_called_once()
            mock_vuln.assert_called_once()
            mock_makedirs.assert_called()
            
            self.assertEqual(result["restoration"], expected_restoration)
            self.assertEqual(result["vulnerabilities"], expected_vulnerability)

    def test_process_optimization_stream(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        mock_stream = io.StringIO(random_stream_data)

        expected_stream_restoration = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_stream_vulnerabilities = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.restorer, 'comprehensive_health_restoration', return_value=expected_stream_restoration) as mock_comp_rest, \
             patch.object(self.optimizer.vulnerability_analyzer, 'parse_stream_data', return_value=expected_stream_vulnerabilities) as mock_parse_stream:

            result = self.optimizer.process_optimization_stream(mock_stream)

            mock_comp_rest.assert_called_once_with(mock_stream)
            mock_parse_stream.assert_called_once_with(mock_stream)

            self.assertEqual(result["stream_restoration"], expected_stream_restoration)
            self.assertEqual(result["stream_vulnerabilities"], expected_stream_vulnerabilities)

    def test_run_optimization_routine(self):
        routine_flag = random.choice([True, False])

        with patch.object(self.optimizer.restorer, 'execute_restoration_routine', return_value=routine_flag) as mock_exec_routine, \
             patch.object(self.optimizer.vulnerability_analyzer, 'scan_vulnerabilities') as mock_scan_vuln:

            result = self.optimizer.run_optimization_routine()

            mock_exec_routine.assert_called_once()
            mock_scan_vuln.assert_called_once()
            self.assertEqual(result, routine_flag)

    def test_optimize_alias(self):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch.object(self.optimizer, 'optimize_repository', return_value=expected_dict) as mock_opt_repo:
            result = self.optimizer.optimize()
            mock_opt_repo.assert_called_once()
            self.assertEqual(result, expected_dict)

    def test_run_alias(self):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch.object(self.optimizer, 'optimize_repository', return_value=expected_dict) as mock_opt_repo:
            result = self.optimizer.run()
            mock_opt_repo.assert_called_once()
            self.assertEqual(result, expected_dict)


if __name__ == '__main__':
    unittest.main()