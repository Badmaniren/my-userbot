import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.repo_performance_optimizer import RepoPerformanceOptimizer

class TestRepoPerformanceOptimizer(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}/{random.randint(1000, 9999)}"
        self.random_threshold = random.uniform(0.1, 99.9)
        self.optimizer = RepoPerformanceOptimizer(repo_path=self.random_repo_path, threshold=self.random_threshold)

    def test_initialization(self):
        self.assertEqual(self.optimizer.repo_path, self.random_repo_path)
        self.assertEqual(self.optimizer.threshold, self.random_threshold)

    def test_composition_execution_success(self):
        expected_profiler_metric = uuid.uuid4().hex
        expected_optimizer_result = uuid.uuid4().hex

        mock_profiler_instance = MagicMock()
        mock_profiler_instance.run_profiling_pipeline.return_value = {
            "status": "profiled",
            "metric": expected_profiler_metric
        }

        mock_health_optimizer_instance = MagicMock()
        mock_health_optimizer_instance.optimize_repository.return_value = {
            "status": "optimized",
            "result": expected_optimizer_result
        }

        with patch('skills.repo_performance_optimizer.RepoPerformanceProfilerPipeline', return_value=mock_profiler_instance) as mock_profiler_cls, \
             patch('skills.repo_performance_optimizer.RepoHealthOptimizer', return_value=mock_health_optimizer_instance) as mock_optimizer_cls:

            result = self.optimizer.optimize_performance()

            mock_profiler_cls.assert_called_once_with(self.random_repo_path, self.random_threshold)
            mock_profiler_instance.run_profiling_pipeline.assert_called_once()

            mock_optimizer_cls.assert_called_once_with(self.random_repo_path)
            mock_health_optimizer_instance.optimize_repository.assert_called_once()

            self.assertIn("profiling", result)
            self.assertIn("optimization", result)
            self.assertEqual(result["profiling"]["metric"], expected_profiler_metric)
            self.assertEqual(result["optimization"]["result"], expected_optimizer_result)

    def test_stream_processing_delegation(self):
        random_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(random_stream_data)
        
        expected_stream_output = {uuid.uuid4().hex: random.randint(1, 100)}

        mock_health_optimizer_instance = MagicMock()
        mock_health_optimizer_instance.process_optimization_stream.return_value = expected_stream_output

        with patch('skills.repo_performance_optimizer.RepoHealthOptimizer', return_value=mock_health_optimizer_instance) as mock_optimizer_cls:
            result = self.optimizer.process_performance_stream(stream_mock)

            mock_optimizer_cls.assert_called_once_with(self.random_repo_path)
            mock_health_optimizer_instance.process_optimization_stream.assert_called_once_with(stream_mock)
            self.assertEqual(result, expected_stream_output)

    def test_routine_execution_boolean(self):
        expected_bool = random.choice([True, False])

        mock_health_optimizer_instance = MagicMock()
        mock_health_optimizer_instance.run_optimization_routine.return_value = expected_bool

        with patch('skills.repo_performance_optimizer.RepoHealthOptimizer', return_value=mock_health_optimizer_instance) as mock_optimizer_cls:
            result = self.optimizer.run_performance_routine()

            mock_optimizer_cls.assert_called_once_with(self.random_repo_path)
            mock_health_optimizer_instance.run_optimization_routine.assert_called_once()
            self.assertEqual(result, expected_bool)

    def test_error_handling_in_pipeline(self):
        random_error_msg = f"error_{uuid.uuid4().hex}"

        with patch('skills.repo_performance_optimizer.RepoPerformanceProfilerPipeline', side_effect=Exception(random_error_msg)) as mock_profiler_cls:
            with self.assertRaises(Exception) as ctx:
                self.optimizer.optimize_performance()
            
            self.assertIn(random_error_msg, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()