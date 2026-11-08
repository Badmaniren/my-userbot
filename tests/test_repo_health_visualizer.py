import os
import json
import uuid
import random
import unittest
from unittest.mock import patch, mock_open, MagicMock
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizer(unittest.TestCase):
    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.pipeline = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.random_prefix = uuid.uuid4().hex[:8]

    def test_repo_health_diagnostic_execution(self):
        repo_path = f"/var/repo_{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        
        result = self.diagnostic.run_diagnostics(repo_path, run_id)
        
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["repo_path"], repo_path)
        self.assertIn("metrics", result)
        self.assertIn("health_score", result["metrics"])
        self.assertIn("complexity", result["metrics"])
        self.assertIn("issues", result["metrics"])

    def test_repo_health_diagnostic_auto_run_id(self):
        repo_path = f"/home/user/project_{uuid.uuid4().hex}"
        
        result = self.diagnostic.run_diagnostics(repo_path)
        
        self.assertIsNotNone(result["run_id"])
        self.assertEqual(result["repo_path"], repo_path)

    def test_repo_health_diagnostic_analyze_alias(self):
        repo_path = f"/opt/src_{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        
        result = self.diagnostic.analyze(repo_path, run_id)
        
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["repo_path"], repo_path)

    def test_repo_health_predictor_pipeline_execution(self):
        diag_data = {
            "run_id": uuid.uuid4().hex,
            "repo_path": f"/tmp/repo_{uuid.uuid4().hex}",
            "metrics": {"health_score": random.random()}
        }
        seed_val = random.randint(1, 1000)
        
        result = self.pipeline.execute_pipeline(diag_data, seed=seed_val)
        
        self.assertEqual(result["diagnostic_data"], diag_data)
        self.assertEqual(result["seed"], seed_val)
        self.assertEqual(result["run_id"], diag_data["run_id"])
        self.assertIn("prediction", result)
        self.assertIn("risk_level", result["prediction"])
        self.assertIn("score", result["prediction"])
        self.assertIn(result["prediction"]["risk_level"], ["LOW", "HIGH"])

    def test_repo_health_visualizer_generation_json(self):
        run_id = uuid.uuid4().hex
        repo_path = f"/srv/git/{uuid.uuid4().hex}"
        target_dir = f"./tmp_dir_{uuid.uuid4().hex[:6]}"
        format_type = "json"
        
        prediction_data = {
            "run_id": run_id,
            "diagnostic_data": {"repo_path": repo_path},
            "prediction": {"risk_level": random.choice(["LOW", "HIGH"]), "score": random.random()}
        }
        
        mock_file = mock_open()
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file):
            
            result = self.visualizer.generate_visualization(
                prediction_data, 
                output_format=format_type, 
                target_directory=target_dir, 
                run_identifier=run_id
            )
            
            mock_makedirs.assert_called_once_with(target_dir, exist_ok=True)
            mock_file.assert_called_once_with(os.path.join(target_dir, f"visualization_{run_id}.json"), "w", encoding="utf-8")
            
            handle = mock_file()
            handle.write.assert_called_once()
            written_content = handle.write.call_args[0][0]
            
            self.assertIn(run_id, written_content)
            self.assertIn(repo_path, written_content)
            
            self.assertEqual(result["format"], format_type)
            self.assertEqual(result["run_id"], run_id)
            self.assertTrue(result["file_path"].endswith(f".{format_type}"))

    def test_repo_health_visualizer_fallback_format(self):
        run_id = uuid.uuid4().hex
        invalid_format = f"ext_{uuid.uuid4().hex[:4]}"
        target_dir = f"./dir_{uuid.uuid4().hex[:6]}"
        
        prediction_data = {
            "run_id": run_id,
            "diagnostic_data": {"repo_path": f"/path/{uuid.uuid4().hex}"}
        }
        
        mock_file = mock_open()
        with patch("os.makedirs"), patch("builtins.open", mock_file):
            result = self.visualizer.generate_visualization(
                prediction_data,
                output_format=invalid_format,
                target_directory=target_dir
            )
            
            self.assertEqual(result["format"], "json")
            mock_file.assert_called_once_with(os.path.join(target_dir, f"visualization_{run_id}.json"), "w", encoding="utf-8")