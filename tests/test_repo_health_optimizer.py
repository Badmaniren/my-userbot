import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.repo_health_optimizer import RepoHealthOptimizer


class TestRepoHealthOptimizer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"

    def test_init_and_public_signatures(self):
        optimizer = RepoHealthOptimizer(self.repo_path)
        self.assertEqual(optimizer.repo_path, self.repo_path)
        self.assertIsNotNone(optimizer.restorer)
        self.assertIsNotNone(optimizer.vulnerability_analyzer)

    def test_optimize_repository_composition(self):
        optimizer = RepoHealthOptimizer(self.repo_path)
        expected_restoration = {"status": uuid.uuid4().hex}
        expected_vuln = {"vulnerabilities": [uuid.uuid4().hex]}

        with patch.object(optimizer.restorer, 'restore_and_protect', return_value=expected_restoration) as mock_restore, \
             patch.object(optimizer.vulnerability_analyzer, 'run', return_value=expected_vuln) as mock_vuln:
            
            result = optimizer.optimize_repository()
            
            mock_restore.assert_called_once()
            mock_vuln.assert_called_once()
            self.assertEqual(result["restoration"], expected_restoration)
            self.assertEqual(result["vulnerabilities"], expected_vuln)

    def test_optimize_alias(self):
        optimizer = RepoHealthOptimizer(self.repo_path)
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(optimizer, 'optimize_repository', return_value=expected_result) as mock_opt:
            self.assertEqual(optimizer.optimize(), expected_result)
            self.assertEqual(optimizer.run(), expected_result)
            self.assertEqual(mock_opt.call_count, 2)

    def test_process_optimization_stream(self):
        optimizer = RepoHealthOptimizer(self.repo_path)
        mock_stream = io.BytesIO(uuid.uuid4().bytes)
        expected_stream_restoration = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_stream_vuln = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(optimizer.restorer, 'comprehensive_health_restoration', return_value=expected_stream_restoration) as mock_rest_stream, \
             patch.object(optimizer.vulnerability_analyzer, 'parse_stream_data', return_value=expected_stream_vuln) as mock_vuln_stream:
            
            result = optimizer.process_optimization_stream(mock_stream)
            
            mock_rest_stream.assert_called_once_with(mock_stream)
            mock_vuln_stream.assert_called_once_with(mock_stream)
            self.assertEqual(result["stream_restoration"], expected_stream_restoration)
            self.assertEqual(result["stream_vulnerabilities"], expected_stream_vuln)

    def test_run_optimization_routine(self):
        optimizer = RepoHealthOptimizer(self.repo_path)
        routine_flag = random.choice([True, False])

        with patch.object(optimizer.restorer, 'execute_restoration_routine', return_value=routine_flag) as mock_routine, \
             patch.object(optimizer.vulnerability_analyzer, 'scan_vulnerabilities') as mock_scan:
            
            result = optimizer.run_optimization_routine()
            
            mock_routine.assert_called_once()
            mock_scan.assert_called_once()
            self.assertEqual(result, routine_flag)


if __name__ == '__main__':
    unittest.main()