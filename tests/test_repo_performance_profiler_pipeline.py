import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.repo_performance_profiler_pipeline import (
    RepoPerformanceProfilerPipeline,
    repo_performance_profiler_pipeline
)

class TestRepoPerformanceProfilerPipeline(unittest.TestCase):
    def test_repo_performance_profiler_pipeline_class_success(self):
        repo_path = f"/repo/{uuid.uuid4().hex}"
        threshold = random.uniform(0.1, 0.9)
        
        expected_status = uuid.uuid4().hex
        expected_diagnostic = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "health_score": random.uniform(0.5, 1.0)
        }
        expected_threshold_passed = random.choice([True, False])
        stream_content = uuid.uuid4().bytes

        with patch("skills.repo_performance_profiler_pipeline.RepoMonitor") as MockRepoMonitor, \
             patch("skills.repo_performance_profiler_pipeline.RepoHealthDiagnostic") as MockRepoHealthDiagnostic:
            
            mock_monitor_instance = MockRepoMonitor.return_value
            mock_monitor_instance.check_status.return_value = expected_status

            mock_diagnostic_instance = MockRepoHealthDiagnostic.return_value
            mock_diagnostic_instance.perform_deep_health_check.return_value = expected_diagnostic
            mock_diagnostic_instance.evaluate_threshold.return_value = expected_threshold_passed
            
            mock_stream = io.BytesIO(stream_content)
            mock_diagnostic_instance.export_report_stream.return_value = mock_stream

            pipeline = RepoPerformanceProfilerPipeline(repo_path, threshold)
            result = pipeline.run_profiling_pipeline()

            MockRepoMonitor.assert_called_once_with(repo_path)
            mock_monitor_instance.check_status.assert_called_once()
            
            MockRepoHealthDiagnostic.assert_called_once()
            mock_diagnostic_instance.perform_deep_health_check.assert_called_once_with(repo_path, threshold)
            
            metric_key = list(expected_diagnostic.keys())[0]
            mock_diagnostic_instance.evaluate_threshold.assert_called_once_with(
                expected_diagnostic, metric_key, threshold
            )
            mock_diagnostic_instance.export_report_stream.assert_called_once_with(repo_path)

            self.assertEqual(result["repo_status"], expected_status)
            self.assertEqual(result["diagnostic_results"], expected_diagnostic)
            self.assertEqual(result["threshold_passed"], expected_threshold_passed)
            self.assertEqual(result["report_stream_content"], stream_content)

    def test_repo_performance_profiler_pipeline_class_empty_diagnostic_keys(self):
        repo_path = f"/var/git/{uuid.uuid4().hex}"
        threshold = random.uniform(0.2, 0.8)
        
        expected_status = uuid.uuid4().hex
        expected_diagnostic = {"status": uuid.uuid4().hex}
        expected_threshold_passed = random.choice([True, False])
        stream_content = uuid.uuid4().bytes

        with patch("skills.repo_performance_profiler_pipeline.RepoMonitor") as MockRepoMonitor, \
             patch("skills.repo_performance_profiler_pipeline.RepoHealthDiagnostic") as MockRepoHealthDiagnostic:
            
            mock_monitor_instance = MockRepoMonitor.return_value
            mock_monitor_instance.check_status.return_value = expected_status

            mock_diagnostic_instance = MockRepoHealthDiagnostic.return_value
            mock_diagnostic_instance.perform_deep_health_check.return_value = expected_diagnostic
            mock_diagnostic_instance.evaluate_threshold.return_value = expected_threshold_passed
            
            mock_stream = io.BytesIO(stream_content)
            mock_diagnostic_instance.export_report_stream.return_value = mock_stream

            pipeline = RepoPerformanceProfilerPipeline(repo_path, threshold)
            result = pipeline.run_profiling_pipeline()

            mock_diagnostic_instance.evaluate_threshold.assert_called_once_with(
                expected_diagnostic, "health_score", threshold
            )
            self.assertEqual(result["report_stream_content"], stream_content)

    def test_repo_performance_profiler_pipeline_function_success(self):
        repo_path = f"/opt/repo_{uuid.uuid4().hex}"
        profiling_id = uuid.uuid4().hex
        threshold = random.uniform(0.3, 0.99)
        
        monitor_status = uuid.uuid4().hex
        diagnostic_data = {uuid.uuid4().hex: random.randint(10, 100)}
        is_performant = random.choice([True, False])

        with patch("skills.repo_performance_profiler_pipeline.RepoMonitor") as MockRepoMonitor, \
             patch("skills.repo_performance_profiler_pipeline.RepoHealthDiagnostic") as MockRepoHealthDiagnostic:
            
            mock_monitor_instance = MockRepoMonitor.return_value
            mock_monitor_instance.check_status.return_value = monitor_status

            mock_diagnostic_instance = MockRepoHealthDiagnostic.return_value
            mock_diagnostic_instance.run_full_diagnostic.return_value = diagnostic_data
            mock_diagnostic_instance.evaluate_threshold.return_value = is_performant

            result = repo_performance_profiler_pipeline(repo_path, profiling_id, threshold)

            MockRepoMonitor.assert_called_once_with(repo_path)
            mock_monitor_instance.check_status.assert_called_once()

            MockRepoHealthDiagnostic.assert_called_once()
            mock_diagnostic_instance.run_full_diagnostic.assert_called_once_with(repo_path)
            mock_diagnostic_instance.evaluate_threshold.assert_called_once_with(
                diagnostic_data, "health_score", threshold
            )

            self.assertEqual(result["profiling_id"], profiling_id)
            self.assertEqual(result["monitor_status"], monitor_status)
            self.assertEqual(result["diagnostic_data"], diagnostic_data)
            self.assertEqual(result["is_performant"], is_performant)


if __name__ == "__main__":
    unittest.main()