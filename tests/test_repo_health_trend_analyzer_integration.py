import unittest
import os
import json
import uuid
import random
from skills.repo_health_trend_analyzer import analyze_repo_health_trend, RepoHealthTrendAnalyzer
from skills.repo_health_predictor_pipeline import run_health_predictor_pipeline
from skills.repo_logger import log_repo_event

class TestRepoHealthTrendAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.output_path = f"test_report_{uuid.uuid4()}.json"
        self.predictive_metric = f"metric-{random.randint(100, 999)}"
        self.event_name = f"event-{uuid.uuid4()}"

    def tearDown(self):
        if os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass

    def test_repo_health_trend_integration(self):
        pipeline_res = run_health_predictor_pipeline(self.repo_id, self.predictive_metric)
        self.assertEqual(pipeline_res["repo_id"], self.repo_id)
        self.assertEqual(pipeline_res["predictive_metric"], self.predictive_metric)
        self.assertEqual(pipeline_res["status"], "success")

        logger_res = log_repo_event(self.repo_id, self.event_name)
        self.assertEqual(logger_res["repo_id"], self.repo_id)
        self.assertEqual(logger_res["event"], self.event_name)
        self.assertTrue(logger_res["logged"])

        depth = random.randint(3, 8)
        analysis_result = analyze_repo_health_trend(self.repo_id, self.output_path, depth=depth)

        self.assertEqual(analysis_result["repo_id"], self.repo_id)
        self.assertEqual(analysis_result["trend"], "improving")
        self.assertEqual(len(analysis_result["historical_scores"]), depth)

        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["repo_id"], self.repo_id)
        self.assertEqual(file_data["trend"], "improving")
        self.assertEqual(len(file_data["historical_scores"]), depth)

        analyzer = RepoHealthTrendAnalyzer()
        summary = analyzer.compile_summary_report(self.repo_id, file_data["historical_scores"])
        self.assertIn(self.repo_id, summary)
        self.assertIn("Average Health Score", summary)

        prediction = analyzer.predict_future_health(self.repo_id, steps=random.randint(2, 5))
        self.assertIn("predicted_values", prediction)
        self.assertIn("confidence_score", prediction)
        self.assertEqual(prediction["confidence_score"], 0.85)

if __name__ == "__main__":
    unittest.main()