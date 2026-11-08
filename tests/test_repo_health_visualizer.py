import os
import json
import uuid
import random
import unittest
from unittest.mock import patch, mock_open
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerModule(unittest.TestCase):
    
    def test_repo_health_diagnostic_run_diagnostics(self):
        diagnostic = RepoHealthDiagnostic()
        rand_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        rand_run_id = uuid.uuid4().hex
        
        result = diagnostic.run_diagnostics(rand_repo, run_id=rand_run_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), rand_run_id)
        self.assertEqual(result.get("repo_path"), rand_repo)
        self.assertIn("metrics", result)
        
        metrics = result["metrics"]
        self.assertIsInstance(metrics.get("health_score"), float)
        self.assertIsInstance(metrics.get("complexity"), int)
        self.assertIsInstance(metrics.get("issues"), int)

    def test_repo_health_diagnostic_run_diagnostics_default_run_id(self):
        diagnostic = RepoHealthDiagnostic()
        rand_repo = f"/var/repo/{uuid.uuid4().hex}"
        
        result = diagnostic.run_diagnostics(rand_repo)
        
        self.assertIsInstance(result, dict)
        self.assertIsNotNone(result.get("run_id"))
        self.assertEqual(result.get("repo_path"), rand_repo)

    def test_repo_health_diagnostic_analyze(self):
        diagnostic = RepoHealthDiagnostic()
        rand_repo = f"/opt/repo_{uuid.uuid4().hex}"
        rand_run_id = uuid.uuid4().hex
        
        result = diagnostic.analyze(rand_repo, run_id=rand_run_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), rand_run_id)
        self.assertEqual(result.get("repo_path"), rand_repo)

    def test_repo_health_predictor_pipeline_execute(self):
        pipeline = RepoHealthPredictorPipeline()
        rand_run_id = uuid.uuid4().hex
        rand_repo = f"/home/user/{uuid.uuid4().hex}"
        
        diagnostic_data = {
            "run_id": rand_run_id,
            "repo_path": rand_repo,
            "metrics": {
                "health_score": random.random(),
                "complexity": random.randint(1, 50),
                "issues": random.randint(0, 5)
            }
        }
        
        rand_seed = random.randint(1, 1000)
        result = pipeline.execute_pipeline(diagnostic_data, seed=rand_seed)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("diagnostic_data"), diagnostic_data)
        self.assertEqual(result.get("seed"), rand_seed)
        self.assertEqual(result.get("run_id"), rand_run_id)
        self.assertIn("prediction", result)
        
        prediction = result["prediction"]
        self.assertIn(prediction.get("risk_level"), ["LOW", "HIGH"])
        self.assertIsInstance(prediction.get("score"), float)

    def test_repo_health_visualizer_generate_visualization(self):
        visualizer = RepoHealthVisualizer()
        rand_run_id = uuid.uuid4().hex
        rand_repo = f"/path/to/{uuid.uuid4().hex}"
        rand_format = random.choice(["png", "svg", "json", "html"])
        rand_dir = f"./temp_dir_{uuid.uuid4().hex}"
        
        prediction_data = {
            "run_id": rand_run_id,
            "diagnostic_data": {
                "repo_path": rand_repo,
                "metrics": {"health_score": 0.85}
            },
            "prediction": {
                "risk_level": "LOW",
                "score": 0.12
            }
        }
        
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            
            result = visualizer.generate_visualization(
                prediction_data=prediction_data,
                output_format=rand_format,
                target_directory=rand_dir,
                run_identifier=rand_run_id
            )
            
            mock_makedirs.assert_called_once_with(rand_dir, exist_ok=True)
            mock_file.assert_called_once()
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("run_id"), rand_run_id)
            self.assertEqual(result.get("format"), rand_format)
            self.assertTrue(result.get("file_path").endswith(f".{rand_format}"))

    def test_repo_health_visualizer_invalid_format_fallback(self):
        visualizer = RepoHealthVisualizer()
        rand_run_id = uuid.uuid4().hex
        rand_bad_format = uuid.uuid4().hex[:5]
        rand_dir = f"./dir_{uuid.uuid4().hex}"
        
        prediction_data = {
            "run_id": rand_run_id,
            "diagnostic_data": {"repo_path": "/dummy/path"}
        }
        
        with patch("os.makedirs"), patch("builtins.open", mock_open()):
            result = visualizer.generate_visualization(
                prediction_data=prediction_data,
                output_format=rand_bad_format,
                target_directory=rand_dir
            )
            
            self.assertEqual(result.get("format"), "json")
            self.assertTrue(result.get("file_path").endswith(".json"))

if __name__ == "__main__":
    unittest.main()