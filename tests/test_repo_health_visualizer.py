import unittest
from unittest.mock import patch
import os
import uuid
import random
import tempfile
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerUnit(unittest.TestCase):
    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.random_repo = f"/repo_{uuid.uuid4().hex}"
        self.random_run_id = uuid.uuid4().hex

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_repo_health_diagnostic_run_diagnostics(self):
        res = self.diagnostic.run_diagnostics(self.random_repo, run_id=self.random_run_id)
        self.assertEqual(res["repo_path"], self.random_repo)
        self.assertEqual(res["run_id"], self.random_run_id)
        self.assertIn("metrics", res)
        self.assertIn("health_score", res["metrics"])
        self.assertIn("complexity", res["metrics"])
        self.assertIn("issues", res["metrics"])

    def test_repo_health_diagnostic_analyze(self):
        res = self.diagnostic.analyze(self.random_repo, run_id=self.random_run_id)
        self.assertEqual(res["repo_path"], self.random_repo)
        self.assertEqual(res["run_id"], self.random_run_id)

    def test_repo_health_predictor_pipeline_execute(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo, run_id=self.random_run_id)
        seed_val = random.randint(1, 1000)
        res = self.predictor.execute_pipeline(diag_data, seed=seed_val)
        self.assertEqual(res["diagnostic_data"], diag_data)
        self.assertEqual(res["run_id"], self.random_run_id)
        self.assertEqual(res["seed"], seed_val)
        self.assertIn("prediction", res)
        self.assertIn("risk_level", res["prediction"])
        self.assertIn("score", res["prediction"])

    def test_repo_health_visualizer_generate_visualization_json(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo, run_id=self.random_run_id)
        pred_data = self.predictor.execute_pipeline(diag_data)
        
        ext = "json"
        res = self.visualizer.generate_visualization(
            prediction_data=pred_data,
            output_format=ext,
            target_directory=self.temp_dir.name,
            run_identifier=self.random_run_id
        )
        
        self.assertEqual(res["format"], ext)
        self.assertEqual(res["run_id"], self.random_run_id)
        self.assertTrue(os.path.exists(res["file_path"]))
        
        with open(res["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(self.random_run_id, content)

    def test_repo_health_visualizer_generate_visualization_invalid_format(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo, run_id=self.random_run_id)
        pred_data = self.predictor.execute_pipeline(diag_data)
        
        invalid_ext = uuid.uuid4().hex[:4]
        res = self.visualizer.generate_visualization(
            prediction_data=pred_data,
            output_format=invalid_ext,
            target_directory=self.temp_dir.name,
            run_identifier=self.random_run_id
        )
        
        self.assertEqual(res["format"], "json")
        self.assertTrue(res["file_path"].endswith(".json"))

    def test_health_visualizer_end_to_end_integration(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo, run_id=self.random_run_id)
        pred_data = self.predictor.execute_pipeline(diag_data, seed=42)
        
        formats = ["png", "svg", "json", "html"]
        chosen_format = random.choice(formats)
        
        res = self.visualizer.generate_visualization(
            prediction_data=pred_data,
            output_format=chosen_format,
            target_directory=self.temp_dir.name,
            run_identifier=self.random_run_id
        )
        
        self.assertEqual(res["run_id"], self.random_run_id)
        self.assertTrue(os.path.exists(res["file_path"]))
        
        with open(res["file_path"], "r", encoding="utf-8") as f:
            data_content = f.read()
            
        self.assertIn(self.random_run_id, data_content)
        self.assertIn(self.random_repo, data_content)