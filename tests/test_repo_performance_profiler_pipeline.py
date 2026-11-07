import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

from skills.repo_performance_profiler_pipeline import RepoPerformanceProfilerPipeline

class TestRepoPerformanceProfilerPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.rand_threshold = round(random.uniform(0.1, 99.9), 2)
        self.rand_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.rand_status = ''.join(random.choices(string.ascii_letters, k=10))
        self.rand_diagnostic_data = {
            self.rand_metric_key: round(random.uniform(1.0, 50.0), 2),
            "status": self.rand_status
        }
        self.pipeline = RepoPerformanceProfilerPipeline(
            repo_path=self.rand_repo_path,
            threshold=self.rand_threshold
        )

    def test_initialization(self):
        self.assertEqual(self.pipeline.repo_path, self.rand_repo_path)
        self.assertEqual(self.pipeline.threshold, self.rand_threshold)

    def test_composition_execution_success(self):
        rand_commit_msg = f"Commit {uuid.uuid4().hex}"
        rand_report_content = f"Report data stream {uuid.uuid4().hex}"
        
        with patch('skills.repo_performance_profiler_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_performance_profiler_pipeline.RepoHealthDiagnostic') as mock_diagnostic_cls:
            
            mock_monitor_instance = mock_monitor_cls.return_value
            mock_monitor_instance.check_status.return_value = self.rand_status
            
            mock_diagnostic_instance = mock_diagnostic_cls.return_value
            mock_diagnostic_instance.perform_deep_health_check.return_value = self.rand_diagnostic_data
            mock_diagnostic_instance.evaluate_threshold.return_value = True
            
            mock_stream = io.StringIO(rand_report_content)
            mock_diagnostic_instance.export_report_stream.return_value = mock_stream

            result = self.pipeline.run_profiling_pipeline()

            mock_monitor_cls.assert_called_once_with(self.rand_repo_path)
            mock_monitor_instance.check_status.assert_called_once()
            
            mock_diagnostic_cls.assert_called_once()
            mock_diagnostic_instance.perform_deep_health_check.assert_called_once_with(
                self.rand_repo_path, self.rand_threshold
            )
            mock_diagnostic_instance.evaluate_threshold.assert_called_once_with(
                self.rand_diagnostic_data, self.rand_metric_key, self.rand_threshold
            )
            mock_diagnostic_instance.export_report_stream.assert_called_once_with(self.rand_repo_path)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("repo_status"), self.rand_status)
            self.assertEqual(result.get("diagnostic_results"), self.rand_diagnostic_data)
            self.assertTrue(result.get("threshold_passed"))
            self.assertEqual(result.get("report_stream_content"), rand_report_content)

    def test_composition_execution_threshold_failed(self):
        with patch('skills.repo_performance_profiler_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_performance_profiler_pipeline.RepoHealthDiagnostic') as mock_diagnostic_cls:
            
            mock_monitor_instance = mock_monitor_cls.return_value
            mock_monitor_instance.check_status.return_value = self.rand_status
            
            mock_diagnostic_instance = mock_diagnostic_cls.return_value
            mock_diagnostic_instance.perform_deep_health_check.return_value = self.rand_diagnostic_data
            mock_diagnostic_instance.evaluate_threshold.return_value = False
            
            mock_stream = io.StringIO(f"Failed threshold stream {uuid.uuid4().hex}")
            mock_diagnostic_instance.export_report_stream.return_value = mock_stream

            result = self.pipeline.run_profiling_pipeline()

            self.assertFalse(result.get("threshold_passed"))
            self.assertEqual(result.get("repo_status"), self.rand_status)
            self.assertEqual(result.get("diagnostic_results"), self.rand_diagnostic_data)

    def test_monitor_exception_handling(self):
        rand_error_msg = f"Error {uuid.uuid4().hex}"
        
        with patch('skills.repo_performance_profiler_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_performance_profiler_pipeline.RepoHealthDiagnostic') as mock_diagnostic_cls:
            
            mock_monitor_instance = mock_monitor_cls.return_value
            mock_monitor_instance.check_status.side_effect = Exception(rand_error_msg)

            with self.assertRaises(Exception) as ctx:
                self.pipeline.run_profiling_pipeline()
            
            self.assertIn(rand_error_msg, str(ctx.exception))
            mock_diagnostic_cls.assert_not_called()

if __name__ == '__main__':
    unittest.main()