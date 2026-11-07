import unittest
import uuid
import tempfile
import shutil
import os
from skills.repo_performance_profiler_pipeline import (
    RepoPerformanceProfilerPipeline,
    repo_performance_profiler_pipeline
)

class TestRepoPerformanceProfilerPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.profiling_id = str(uuid.uuid4())
        self.threshold = float(uuid.uuid4().int % 100) / 10.0

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_performance_profiler_pipeline_class(self):
        pipeline = RepoPerformanceProfilerPipeline(self.repo_path, self.threshold)
        result = pipeline.run_profiling_pipeline()
        
        self.assertIsInstance(result, dict)
        self.assertIn("repo_status", result)
        self.assertIn("diagnostic_results", result)
        self.assertIn("threshold_passed", result)
        self.assertIn("report_stream_content", result)
        self.assertIsInstance(result["threshold_passed"], bool)

    def test_repo_performance_profiler_pipeline_function(self):
        result = repo_performance_profiler_pipeline(
            self.repo_path, 
            self.profiling_id, 
            self.threshold
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("profiling_id"), self.profiling_id)
        self.assertIn("monitor_status", result)
        self.assertIn("diagnostic_data", result)
        self.assertIn("is_performant", result)
        self.assertIsInstance(result["is_performant"], bool)

if __name__ == "__main__":
    unittest.main()