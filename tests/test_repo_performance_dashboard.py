import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_performance_dashboard import RepoPerformanceDashboard


class TestRepoPerformanceDashboard(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex[:8]}"
        self.random_threshold = round(random.uniform(0.1, 99.9), 2)
        self.random_output_path = f"/reports/{uuid.uuid4().hex[:8]}.txt"
        self.random_status = random.choice(["SUCCESS", "WARNING", "CRITICAL", "OPTIMIZED"])
        self.random_summary = f"Summary report data: {uuid.uuid4().hex}"
        self.random_report_content = f"Report content stream {uuid.uuid4().hex}"

    @patch("skills.repo_performance_dashboard.RepoReporter")
    @patch("skills.repo_performance_dashboard.RepoPerformanceOptimizer")
    def test_dashboard_initialization_and_composition(self, mock_optimizer_class, mock_reporter_class):
        mock_reporter_instance = mock_reporter_class.return_value
        mock_optimizer_instance = mock_optimizer_class.return_value

        dashboard = RepoPerformanceDashboard(
            repo_path=self.random_repo_path,
            threshold=self.random_threshold
        )

        mock_reporter_class.assert_called_once_with(repo_path=self.random_repo_path)
        mock_optimizer_class.assert_called_once_with(
            repo_path=self.random_repo_path,
            threshold=self.random_threshold
        )
        self.assertEqual(dashboard.reporter, mock_reporter_instance)
        self.assertEqual(dashboard.optimizer, mock_optimizer_instance)

    @patch("skills.repo_performance_dashboard.RepoReporter")
    @patch("skills.repo_performance_dashboard.RepoPerformanceOptimizer")
    def test_generate_live_dashboard_report(self, mock_optimizer_class, mock_reporter_class):
        mock_reporter_instance = mock_reporter_class.return_value
        mock_optimizer_instance = mock_optimizer_class.return_value

        random_opt_result = {
            "status": self.random_status,
            "metrics": {uuid.uuid4().hex: random.randint(1, 100)},
            "optimized": True
        }
        mock_optimizer_instance.optimize_performance.return_value = random_opt_result
        mock_reporter_instance.generate_report.return_value = self.random_output_path

        dashboard = RepoPerformanceDashboard(
            repo_path=self.random_repo_path,
            threshold=self.random_threshold
        )

        result_path = dashboard.generate_live_dashboard_report(output_path=self.random_output_path)

        mock_optimizer_instance.optimize_performance.assert_called_once()
        mock_reporter_instance.generate_report.assert_called_once_with(
            status=random_opt_result["status"],
            summary=str(random_opt_result),
            output_path=self.random_output_path
        )
        self.assertEqual(result_path, self.random_output_path)

    @patch("skills.repo_performance_dashboard.RepoReporter")
    @patch("skills.repo_performance_dashboard.RepoPerformanceOptimizer")
    def test_process_performance_stream_and_finalize(self, mock_optimizer_class, mock_reporter_class):
        mock_reporter_instance = mock_reporter_class.return_value
        mock_optimizer_instance = mock_optimizer_class.return_value

        stream_key = uuid.uuid4().hex
        stream_val = random.randint(500, 5000)
        stream_data = {stream_key: stream_val}

        mock_optimizer_instance.run_performance_routine.return_value = True
        mock_reporter_instance.generate_final_report.return_value = self.random_report_content

        dashboard = RepoPerformanceDashboard(
            repo_path=self.random_repo_path,
            threshold=self.random_threshold
        )

        dashboard.process_performance_stream(stream_data)
        mock_optimizer_instance.process_performance_stream.assert_called_once_with(stream_data)
        mock_optimizer_instance.run_performance_routine.assert_called_once()

        final_report = dashboard.finalize_dashboard_report(file_path=self.random_output_path)

        mock_reporter_instance.save_report.assert_called_once_with(
            file_path=self.random_output_path,
            content=self.random_report_content
        )
        self.assertEqual(final_report, self.random_report_content)

    @patch("skills.repo_performance_dashboard.RepoReporter")
    @patch("skills.repo_performance_dashboard.RepoPerformanceOptimizer")
    def test_run_full_optimization_pipeline(self, mock_optimizer_class, mock_reporter_class):
        mock_optimizer_instance = mock_optimizer_class.return_value
        
        expected_pipeline_result = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "success": True
        }
        mock_optimizer_instance.run_performance_optimization_pipeline.return_value = expected_pipeline_result

        dashboard = RepoPerformanceDashboard(
            repo_path=self.random_repo_path,
            threshold=self.random_threshold
        )

        pipeline_result = dashboard.run_full_optimization_pipeline()

        mock_optimizer_instance.run_performance_optimization_pipeline.assert_called_once()
        self.assertEqual(pipeline_result, expected_pipeline_result)