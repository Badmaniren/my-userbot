import unittest
import os
import json
import uuid
import random
import tempfile

from skills.repo_health_collector import collect_repo_health_metrics
from skills.repo_health_trend_calculator import calculate_repo_health_trends
from skills.repo_health_analytics_reporter import (
    RepoHealthAnalyticsReporter,
    generate_and_export_repo_health_analytics_report
)

class TestRepoHealthAnalyticsReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_id = f"repo-{uuid.uuid4()}"
        
        # Генерация случайных метрик для реального взаимодействия навыков
        self.raw_metrics_input = {
            "commits_count": random.randint(10, 500),
            "open_issues": random.randint(0, 50),
            "pull_requests_merged": random.randint(5, 100),
            "code_coverage": round(random.uniform(50.0, 99.9), 2)
        }
        
        # Используем смежные реальные навыки согласно правилу отсутствия моков
        self.collected_data = collect_repo_health_metrics(
            repo_id=self.repo_id,
            raw_metrics=self.raw_metrics_input
        )
        
        self.trend_data = calculate_repo_health_trends(
            repo_id=self.repo_id,
            metrics=self.collected_data
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_generate_and_export_pipeline_integration(self):
        random_filename = f"report_{uuid.uuid4()}.json"
        destination_file = os.path.join(self.test_dir.name, random_filename)
        
        result = generate_and_export_repo_health_analytics_report(
            repo_id=self.repo_id,
            collected_metrics=self.collected_data,
            trend_analysis=self.trend_data,
            destination_file=destination_file
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["destination_file"], destination_file)
        
        self.assertTrue(os.path.exists(destination_file))
        
        with open(destination_file, "r", encoding="utf-8") as f:
            file_content = json.load(f)
            
        self.assertEqual(file_content["details"]["repository"], self.repo_id)
        self.assertIn("trend_analysis", file_content)
        self.assertIn("analytics", file_content)
        self.assertIn("calculated_score", file_content["analytics"])

    def test_reporter_streams_and_exceptions(self):
        reporter = RepoHealthAnalyticsReporter()
        
        report_input = {
            "repository": self.repo_id,
            "metrics": self.raw_metrics_input,
            "status": "HEALTHY",
            "timestamp": 1600000000
        }
        
        report_data = reporter.generate_report(report_input)
        stream = reporter.export_to_stream(report_data, format="bytes")
        
        stream_content = json.loads(stream.getvalue().decode("utf-8"))
        self.assertEqual(stream_content["details"]["repository"], self.repo_id)
        
        with self.assertRaises(TypeError):
            reporter.generate_report("invalid_data_type")
            
        with self.assertRaises(KeyError):
            reporter.generate_report({"repository": self.repo_id})
            
        with self.assertRaises(ValueError):
            reporter.generate_report({
                "repository": self.repo_id,
                "metrics": {},
                "status": "HEALTHY",
                "timestamp": 1600000000
            })
            
        with self.assertRaises(ValueError):
            reporter.export_report(report_data, os.path.join(self.test_dir.name, "fail.txt"), format="xml")

if __name__ == "__main__":
    unittest.main()