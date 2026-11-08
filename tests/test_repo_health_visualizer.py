import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import string
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerSuite(unittest.TestCase):

    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.pipeline = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        
        self.random_repo_path = f"/path/to/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_run_id = uuid.uuid4().hex
        self.random_seed = random.randint(1, 10000)

    def test_repo_health_diagnostic_run(self):
        result = self.diagnostic.run_diagnostics(self.random_repo_path, self.random_run_id)
        
        self.assertEqual(result["run_id"], self.random_run_id)
        self.assertEqual(result["repo_path"], self.random_repo_path)
        self.assertIn("metrics", result)
        self.assertIn("health_score", result["metrics"])
        self.assertIn("complexity", result["metrics"])
        self.assertIn("issues", result["metrics"])
        
        self.assertGreaterEqual(result["metrics"]["health_score"], 0.0)
        self.assertLessEqual(result["metrics"]["health_score"], 1.0)
        self.assertGreaterEqual(result["metrics"]["complexity"], 1)
        self.assertLessEqual(result["metrics"]["complexity"], 100)
        self.assertGreaterEqual(result["metrics"]["issues"], 0)
        self.assertLessEqual(result["metrics"]["issues"], 10)

    def test_repo_health_diagnostic_auto_id(self):
        result = self.diagnostic.run_diagnostics(self.random_repo_path)
        self.assertIsNotNone(result["run_id"])
        self.assertIsInstance(result["run_id"], str)
        self.assertEqual(result["repo_path"], self.random_repo_path)

    def test_repo_health_diagnostic_analyze_alias(self):
        diag_result = self.diagnostic.run_diagnostics(self.random_repo_path, self.random_run_id)
        analyze_result = self.diagnostic.analyze(self.random_repo_path, self.random_run_id)
        
        self.assertEqual(diag_result["run_id"], analyze_result["run_id"])
        self.assertEqual(diag_result["repo_path"], analyze_result["repo_path"])

    def test_repo_health_predictor_pipeline_execution(self):
        diagnostic_data = self.diagnostic.run_diagnostics(self.random_repo_path, self.random_run_id)
        pipeline_result = self.pipeline.execute_pipeline(diagnostic_data, seed=self.random_seed)
        
        self.assertEqual(pipeline_result["run_id"], self.random_run_id)
        self.assertEqual(pipeline_result["seed"], self.random_seed)
        self.assertEqual(pipeline_result["diagnostic_data"], diagnostic_data)
        self.assertIn("prediction", pipeline_result)
        self.assertIn("risk_level", pipeline_result["prediction"])
        self.assertIn("score", pipeline_result["prediction"])
        self.assertIn(pipeline_result["prediction"]["risk_level"], ["LOW", "HIGH"])

    def test_repo_health_visualizer_generation_valid_format(self):
        diagnostic_data = self.diagnostic.run_diagnostics(self.random_repo_path, self.random_run_id)
        pipeline_result = self.pipeline.execute_pipeline(diagnostic_data, seed=self.random_seed)
        
        valid_formats = ["png", "svg", "json", "html"]
        chosen_format = random.choice(valid_formats)
        target_dir = f"./tmp_{uuid.uuid4().hex}"
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file), patch("os.makedirs") as mock_makedirs:
            result = self.visualizer.generate_visualization(
                prediction_data=pipeline_result,
                output_format=chosen_format,
                target_directory=target_dir,
                run_identifier=self.random_run_id
            )
            
            mock_makedirs.assert_called_once_with(target_dir, exist_ok=True)
            mock_file.assert_called_once()
            
            self.assertEqual(result["format"], chosen_format)
            self.assertEqual(result["run_id"], self.random_run_id)
            self.assertTrue(result["file_path"].endswith(f".{chosen_format}"))
            self.assertIn(self.random_run_id, result["file_path"])

    def test_repo_health_visualizer_generation_invalid_format_fallback(self):
        diagnostic_data = self.diagnostic.run_diagnostics(self.random_repo_path, self.random_run_id)
        pipeline_result = self.pipeline.execute_pipeline(diagnostic_data, seed=self.random_seed)
        
        invalid_format = ''.join(random.choices(string.ascii_lowercase, k=6))
        target_dir = f"./tmp_{uuid.uuid4().hex}"
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file), patch("os.makedirs"):
            result = self.visualizer.generate_visualization(
                prediction_data=pipeline_result,
                output_format=invalid_format,
                target_directory=target_dir,
                run_identifier=self.random_run_id
            )
            
            self.assertEqual(result["format"], "json")
            self.assertTrue(result["file_path"].endswith(".json"))

    def test_repo_health_visualizer_missing_identifiers(self):
        random_payload_key = uuid.uuid4().hex
        random_payload_val = uuid.uuid4().hex
        minimal_prediction_data = {
            random_payload_key: random_payload_val
        }
        
        target_dir = f"./tmp_{uuid.uuid4().hex}"
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file), patch("os.makedirs"):
            result = self.visualizer.generate_visualization(
                prediction_data=minimal_prediction_data,
                output_format="json",
                target_directory=target_dir,
                run_identifier=None
            )
            
            self.assertIsNotNone(result["run_id"])
            self.assertTrue(len(result["run_id"]) > 0)
            self.assertEqual(result["format"], "json")

if __name__ == "__main__":
    unittest.main()