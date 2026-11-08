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
    def test_repo_health_diagnostic_run(self):
        diagnostic = RepoHealthDiagnostic()
        rand_path = f"/var/repo/{uuid.uuid4().hex}"
        rand_run_id = uuid.uuid4().hex
        
        result = diagnostic.run_diagnostics(rand_path, rand_run_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), rand_run_id)
        self.assertEqual(result.get("repo_path"), rand_path)
        self.assertIn("metrics", result)
        self.assertIsInstance(result["metrics"].get("health_score"), float)
        self.assertIsInstance(result["metrics"].get("complexity"), int)
        self.assertIsInstance(result["metrics"].get("issues"), int)

    def test_repo_health_diagnostic_analyze_fallback_run_id(self):
        diagnostic = RepoHealthDiagnostic()
        rand_path = f"/tmp/{uuid.uuid4().hex}"
        
        result = diagnostic.analyze(rand_path)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_path"), rand_path)
        self.assertIsNotNone(result.get("run_id"))

    def test_repo_health_predictor_pipeline_execution(self):
        pipeline = RepoHealthPredictorPipeline()
        rand_run_id = uuid.uuid4().hex
        rand_path = f"/home/user/repo_{uuid.uuid4().hex}"
        rand_seed = random.randint(1, 99999)
        
        diagnostic_data = {
            "run_id": rand_run_id,
            "repo_path": rand_path,
            "metrics": {
                "health_score": random.random(),
                "complexity": random.randint(10, 50),
                "issues": random.randint(0, 5)
            }
        }
        
        result = pipeline.execute_pipeline(diagnostic_data, seed=rand_seed)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), rand_run_id)
        self.assertEqual(result.get("seed"), rand_seed)
        self.assertIn("prediction", result)
        self.assertIn(result["prediction"].get("risk_level"), ["LOW", "HIGH"])
        self.assertIsInstance(result["prediction"].get("score"), float)

    def test_repo_health_visualizer_generation_valid_format(self):
        visualizer = RepoHealthVisualizer()
        rand_run_id = uuid.uuid4().hex
        rand_path = f"/opt/repos/{uuid.uuid4().hex}"
        rand_dir = f"/tmp/{uuid.uuid4().hex}"
        rand_format = random.choice(["json", "png", "svg", "html"])
        
        prediction_data = {
            "run_id": rand_run_id,
            "diagnostic_data": {
                "repo_path": rand_path,
                "metrics": {"health_score": 0.85}
            },
            "prediction": {
                "risk_level": "LOW",
                "score": 0.123
            }
        }
        
        mock_file = mock_open()
        with patch("os.makedirs"), patch("builtins.open", mock_file):
            result = visualizer.generate_visualization(
                prediction_data=prediction_data,
                output_format=rand_format,
                target_directory=rand_dir,
                run_identifier=rand_run_id
            )
            
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), rand_run_id)
        self.assertEqual(result.get("format"), rand_format)
        self.assertTrue(result.get("file_path").endswith(f".{rand_format}"))
        mock_file.assert_called_once()

    def test_repo_health_visualizer_generation_invalid_format_fallback(self):
        visualizer = RepoHealthVisualizer()
        rand_run_id = uuid.uuid4().hex
        rand_path = f"/var/tmp/{uuid.uuid4().hex}"
        rand_dir = f"/tmp/{uuid.uuid4().hex}"
        invalid_format = uuid.uuid4().hex[:5]
        
        prediction_data = {
            "run_id": rand_run_id,
            "diagnostic_data": {
                "repo_path": rand_path
            }
        }
        
        mock_file = mock_open()
        with patch("os.makedirs"), patch("builtins.open", mock_file):
            result = visualizer.generate_visualization(
                prediction_data=prediction_data,
                output_format=invalid_format,
                target_directory=rand_dir,
                run_identifier=rand_run_id
            )
            
        self.assertEqual(result.get("format"), "json")
        self.assertTrue(result.get("file_path").endswith(".json"))

    def test_repo_health_visualizer_io_error_handling(self):
        visualizer = RepoHealthVisualizer()
        rand_run_id = uuid.uuid4().hex
        prediction_data = {"run_id": rand_run_id, "diagnostic_data": {"repo_path": "/some/path"}}
        
        with patch("os.makedirs"), patch("builtins.open", side_effect=IOError("Disk full")):
            with self.assertRaises(IOError):
                visualizer.generate_visualization(prediction_data)

if __name__ == "__main__":
    unittest.main()