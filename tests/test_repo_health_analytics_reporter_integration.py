import unittest
import os
import uuid
import random
from skills.repo_health_analytics_reporter import generate_and_export_repo_health_analytics_report
from skills.repo_health_collector import collect_repo_health_metrics
from skills.repo_health_trend_calculator import calculate_repo_health_trends

class TestRepoHealthAnalyticsReporterIntegration(unittest.TestCase):
    def test_repo_health_analytics_reporter_integration(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_score_base = random.randint(50, 95)
        
        raw_metrics = collect_repo_health_metrics(
            repo_identifier=unique_repo_id,
            base_score=random_score_base
        )
        
        self.assertIn("metrics", raw_metrics)
        
        trend_data = calculate_repo_health_trends(
            metrics_payload=raw_metrics,
            trend_window_days=random.choice([7, 14, 30])
        )
        
        self.assertIn("trend_coefficient", trend_data)
        
        output_filename = f"report_{uuid.uuid4()}.json"
        
        export_result = generate_and_export_repo_health_analytics_report(
            repo_id=unique_repo_id,
            collected_metrics=raw_metrics,
            trend_analysis=trend_data,
            destination_file=output_filename
        )
        
        self.assertTrue(export_result.get("success", False))
        self.assertEqual(export_result.get("repo_id"), unique_repo_id)
        self.assertTrue(os.path.exists(output_filename))
        
        with open(output_filename, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(unique_repo_id, file_content)
            
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == "__main__":
    unittest.main()