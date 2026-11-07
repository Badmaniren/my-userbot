import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_monitor import repo_monitor
from skills.repo_analytics import repo_analytics
from skills.repo_performance_analyzer import repo_performance_analyzer

class TestRepoPerformanceAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_id = str(uuid.uuid4())
        self.metric_value = random.randint(100, 5000)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_performance_analyzer_integration_real_flow(self):
        monitor_input = {
            "repo_id": self.repo_id,
            "target_path": self.test_dir,
            "cpu_load_metric": self.metric_value,
            "io_wait": random.random() * 10
        }
        
        monitoring_data = repo_monitor(monitor_input)
        self.assertIn("monitoring_id", monitoring_data)

        analytics_input = {
            "repo_id": self.repo_id,
            "monitoring_payload": monitoring_data,
            "depth": random.choice([1, 2, 3])
        }
        
        analytics_result = repo_analytics(analytics_input)
        self.assertIn("analytics_report_id", analytics_result)

        analyzer_input = {
            "repo_id": self.repo_id,
            "analytics_data": analytics_result,
            "threshold": self.metric_value
        }

        performance_report = repo_performance_analyzer(analyzer_input)

        self.assertIn("bottlenecks_identified", performance_report)
        self.assertIn("analysis_id", performance_report)
        self.assertEqual(performance_report["repo_id"], self.repo_id)
        
        report_file_path = os.path.join(self.test_dir, f"perf_report_{self.repo_id}.json")
        self.assertTrue(os.path.exists(report_file_path), "Интеграционный модуль должен создавать реальный артефакт (файл отчета) на диске.")

if __name__ == "__main__":
    unittest.main()