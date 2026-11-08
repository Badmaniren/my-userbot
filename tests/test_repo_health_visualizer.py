import unittest
from unittest.mock import patch
import os
import shutil
import uuid
import random
import json
from skills.repo_health_visualizer import RepoHealthDiagnostic, RepoHealthPredictorPipeline, RepoHealthVisualizer

class TestRepoHealthVisualizerSuite(unittest.TestCase):
    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.test_dir = f"temp_test_dir_{uuid.uuid4().hex}"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_repo_health_diagnostic_execution(self):
        repo_path = f"/path/to/repo_{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        
        result = self.diagnostic.run_diagnostics(repo_path, run_id=run_id)
        
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["repo_path"], repo_path)
        self.assertIn("metrics", result)
        self.assertIn("health_score", result["metrics"])
        self.assertIn("complexity", result["metrics"])
        self.assertIn("issues", result["metrics"])

    def test_repo_health_diagnostic_analyze_alias(self):
        repo_path = f"/another/repo_{uuid.uuid4().hex}"
        
        result = self.diagnostic.analyze(repo_path)
        
        self.assertEqual(result["repo_path"], repo_path)
        self.assertIsNotNone(result["run_id"])

    def test_repo_health_predictor_pipeline_execution(self):
        repo_path = f"/repo_{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        diagnostic_data = self.diagnostic.run_diagnostics(repo_path, run_id=run_id)
        seed = random.randint(1, 1000)
        
        prediction_result = self.predictor.execute_pipeline(diagnostic_data, seed=seed)
        
        self.assertEqual(prediction_result["run_id"], run_id)
        self.assertEqual(prediction_result["seed"], seed)
        self.assertIn("prediction", prediction_result)
        self.assertIn("risk_level", prediction_result["prediction"])
        self.assertIn("score", prediction_result["prediction"])
        self.assertIn(prediction_result["prediction"]["risk_level"], ["LOW", "HIGH"])

    def test_repo_health_visualizer_generates_file_and_content(self):
        repo_path = f"/target/repo_{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        diagnostic_data = self.diagnostic.run_diagnostics(repo_path, run_id=run_id)
        prediction_data = self.predictor.execute_pipeline(diagnostic_data)
        
        output_formats = ["json", "png", "svg", "html"]
        chosen_format = random.choice(output_formats)
        
        vis_result = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=chosen_format,
            target_directory=self.test_dir,
            run_identifier=run_id
        )
        
        self.assertEqual(vis_result["run_id"], run_id)
        self.assertEqual(vis_result["format"], chosen_format)
        self.assertTrue(os.path.exists(vis_result["file_path"]))
        
        with open(vis_result["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn(run_id, content)
        self.assertIn(repo_path, content)

    def test_repo_health_visualizer_invalid_format_fallback(self):
        repo_path = f"/repo/fallback_{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        diagnostic_data = self.diagnostic.run_diagnostics(repo_path, run_id=run_id)
        prediction_data = self.predictor.execute_pipeline(diagnostic_data)
        
        invalid_format = f"ext_{uuid.uuid4().hex[:4]}"
        
        vis_result = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=invalid_format,
            target_directory=self.test_dir,
            run_identifier=run_id
        )
        
        self.assertEqual(vis_result["format"], "json")
        self.assertTrue(vis_result["file_path"].endswith(".json"))
        self.assertTrue(os.path.exists(vis_result["file_path"]))

    def test_repo_health_visualizer_auto_generates_run_id(self):
        repo_path = f"/repo/auto_{uuid.uuid4().hex}"
        diagnostic_data = self.diagnostic.run_diagnostics(repo_path)
        prediction_data = self.predictor.execute_pipeline(diagnostic_data)
        prediction_data.pop("run_id", None)
        
        vis_result = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format="json",
            target_directory=self.test_dir
        )
        
        self.assertIsNotNone(vis_result["run_id"])
        self.assertTrue(os.path.exists(vis_result["file_path"]))

if __name__ == '__main__':
    unittest.main()