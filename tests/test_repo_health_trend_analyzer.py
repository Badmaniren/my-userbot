import unittest
from unittest.mock import patch, MagicMock
import os
import json
import random
import uuid
import io
import requests
from bs4 import BeautifulSoup

from skills.repo_health_predictor_pipeline import run_health_predictor_pipeline
from skills.repo_logger import log_repo_event
from skills.repo_health_trend_analyzer import (
    analyze_repo_health_trend,
    RepoHealthTrendAnalyzer
)

class TestRepoHealthTrendAnalyzer(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4().hex)
        self.predictive_metric = str(uuid.uuid4().hex)
        self.event_name = str(uuid.uuid4().hex)
        self.output_path = f"test_report_{uuid.uuid4().hex}.json"
        self.url = f"http://{uuid.uuid4().hex}.com/api"
        self.element_id = str(uuid.uuid4().hex)
        self.project_name = str(uuid.uuid4().hex)

    def tearDown(self):
        if os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass

    def test_run_health_predictor_pipeline_success(self):
        res = run_health_predictor_pipeline(self.repo_id, self.predictive_metric)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["predictive_metric"], self.predictive_metric)
        self.assertEqual(res["status"], "success")

    def test_log_repo_event_success(self):
        res = log_repo_event(self.repo_id, self.event_name)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["event"], self.event_name)
        self.assertTrue(res["logged"])

    def test_analyze_repo_health_trend_improving(self):
        depth = random.randint(3, 8)
        res = analyze_repo_health_trend(self.repo_id, self.output_path, depth=depth)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["trend"], "improving")
        self.assertEqual(len(res["historical_scores"]), depth)
        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["repo_id"], self.repo_id)
            self.assertEqual(data["trend"], "improving")

    def test_analyze_repo_health_trend_stable_single(self):
        res = analyze_repo_health_trend(self.repo_id, self.output_path, depth=1)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["trend"], "stable")
        self.assertEqual(len(res["historical_scores"]), 1)

    def test_analyzer_class_analyze_trend_improving(self):
        analyzer = RepoHealthTrendAnalyzer()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "repo_id": self.repo_id,
            "metric": self.predictive_metric,
            "historical_scores": [10.0, 20.0, 30.0]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(analyzer.session, "get", return_value=mock_response) as mock_get:
            result = analyzer.analyze_trend(self.url, self.repo_id)
            mock_get.assert_called_once_with(self.url)
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["metric"], self.predictive_metric)
            self.assertEqual(result["trend"], "improving")

    def test_analyzer_class_analyze_trend_declining(self):
        analyzer = RepoHealthTrendAnalyzer()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "repo_id": self.repo_id,
            "metric": self.predictive_metric,
            "historical_scores": [50.0, 30.0, 10.0]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(analyzer.session, "get", return_value=mock_response):
            result = analyzer.analyze_trend(self.url, self.repo_id)
            self.assertEqual(result["trend"], "declining")

    def test_analyzer_class_analyze_trend_stable(self):
        analyzer = RepoHealthTrendAnalyzer()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "repo_id": self.repo_id,
            "metric": self.predictive_metric,
            "historical_scores": [25.0, 25.0]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(analyzer.session, "get", return_value=mock_response):
            result = analyzer.analyze_trend(self.url, self.repo_id)
            self.assertEqual(result["trend"], "stable")

    def test_analyzer_class_analyze_trend_connection_error(self):
        analyzer = RepoHealthTrendAnalyzer()
        with patch.object(analyzer.session, "get", side_effect=requests.exceptions.ConnectionError):
            result = analyzer.analyze_trend(self.url, self.repo_id)
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["error"], "ConnectionError")
            self.assertTrue(result["degraded"])

    def test_extract_trend_from_html_found(self):
        analyzer = RepoHealthTrendAnalyzer()
        status_string = str(uuid.uuid4().hex)
        html_content = f'<html><body><div id="{self.element_id}"><span class="status">{status_string}</span></div></body></html>'

        mock_response = MagicMock()
        mock_response.content = html_content.encode('utf-8')

        with patch("requests.get", return_value=mock_response) as mock_get:
            res = analyzer.extract_trend_from_html(self.url, self.element_id)
            mock_get.assert_called_once_with(self.url)
            self.assertEqual(res["status"], status_string)
            self.assertEqual(res["element_id"], self.element_id)

    def test_extract_trend_from_html_not_found(self):
        analyzer = RepoHealthTrendAnalyzer()
        html_content = '<html><body><div><span>Nothing here</span></div></body></html>'

        mock_response = MagicMock()
        mock_response.content = html_content.encode('utf-8')

        with patch("requests.get", return_value=mock_response):
            res = analyzer.extract_trend_from_html(self.url, self.element_id)
            self.assertEqual(res["status"], "")
            self.assertEqual(res["element_id"], self.element_id)

    def test_predict_future_health(self):
        analyzer = RepoHealthTrendAnalyzer()
        custom_history = [float(random.randint(10, 40)), float(random.randint(41, 80))]
        steps = random.randint(2, 5)

        with patch.object(analyzer, "_fetch_internal_history", return_value=custom_history) as mock_fetch:
            res = analyzer.predict_future_health(self.repo_id, steps=steps)
            mock_fetch.assert_called_once_with(self.repo_id)
            self.assertEqual(len(res["predicted_values"]), steps)
            self.assertEqual(res["confidence_score"], 0.85)
            self.assertEqual(res["predicted_values"][0], custom_history[-1] + 1.0)

    def test_compile_summary_report(self):
        analyzer = RepoHealthTrendAnalyzer()
        scores = [float(random.randint(10, 100)), float(random.randint(10, 100))]
        report = analyzer.compile_summary_report(self.project_name, scores)
        self.assertIn(self.project_name, report)
        self.assertIn("Average Health Score", report)
        self.assertIn(f"Analyzed successfully with {len(scores)} data points", report)

    def test_compile_summary_report_empty(self):
        analyzer = RepoHealthTrendAnalyzer()
        report = analyzer.compile_summary_report(self.project_name, [])
        self.assertIn(self.project_name, report)
        self.assertIn("Average Health Score: 0.00", report)
        self.assertIn("Analyzed successfully with 0 data points", report)

if __name__ == '__main__':
    unittest.main()