import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import json
from skills.repo_health_visualizer import RepoHealthDiagnostic, RepoHealthPredictorPipeline, RepoHealthVisualizer

class TestRepoHealthVisualizerInquisitor(unittest.TestCase):

    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.pipeline = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.random_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_run_id = uuid.uuid4().hex

    def test_repo_health_diagnostic_run(self):
        result = self.diagnostic.run_diagnostics(self.random_repo, self.random_run_id)
        self.assertEqual(result["run_id"], self.random_run_id)
        self.assertEqual(result["repo_path"], self.random_repo)
        self.assertIn("health_score", result["metrics"])
        self.assertIn("complexity", result["metrics"])
        self.assertIn("issues", result["metrics"])

    def test_repo_health_diagnostic_analyze(self):
        result = self.diagnostic.analyze(self.random_repo, self.random_run_id)
        self.assertEqual(result["run_id"], self.random_run_id)
        self.assertEqual(result["repo_path"], self.random_repo)

    def test_repo_health_predictor_pipeline(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo, self.random_run_id)
        seed_val = random.randint(1, 1000)
        pipeline_result = self.pipeline.execute_pipeline(diag_data, seed=seed_val)
        
        self.assertEqual(pipeline_result["diagnostic_data"], diag_data)
        self.assertEqual(pipeline_result["run_id"], self.random_run_id)
        self.assertEqual(pipeline_result["seed"], seed_val)
        self.assertIn("prediction", pipeline_result)
        self.assertIn("risk_level", pipeline_result["prediction"])
        self.assertIn("score", pipeline_result["prediction"])

    def test_repo_health_visualizer_generation(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo, self.random_run_id)
        pipeline_result = self.pipeline.execute_pipeline(diag_data)
        
        exts = ["png", "svg", "json", "html", uuid.uuid4().hex[:3]]
        chosen_ext = random.choice(exts)
        target_dir = f"/tmp/{uuid.uuid4().hex}"

        mock_file_handle = mock_open()
        with patch("builtins.open", mock_file_handle):
            with patch("os.path.join", return_value=f"{target_dir}/file.{chosen_ext}"):
                res = self.visualizer.generate_visualization(
                    prediction_data=pipeline_result,
                    output_format=chosen_ext,
                    target_directory=target_dir,
                    run_identifier=self.random_run_id
                )

        self.assertEqual(res["run_id"], self.random_run_id)
        expected_ext = chosen_ext if chosen_ext in ["png", "svg", "json", "html"] else "json"
        self.assertEqual(res["format"], expected_ext)
        mock_file_handle.assert_called_once()
        
        handle = mock_file_handle()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn(self.random_run_id, written_content)
        self.assertIn(self.random_repo, written_content)

    def test_repo_health_visualizer_fallback_run_id(self):
        diag_data = self.diagnostic.run_diagnostics(self.random_repo)
        pipeline_result = self.pipeline.execute_pipeline(diag_data)
        pipeline_result.pop("run_id", None)
        
        target_dir = f"/tmp/{uuid.uuid4().hex}"
        mock_file_handle = mock_open()
        with patch("builtins.open", mock_file_handle):
            with patch("os.path.join", return_value=f"{target_dir}/file.json"):
                res = self.visualizer.generate_visualization(
                    prediction_data=pipeline_result,
                    output_format="json",
                    target_directory=target_dir
                )

        self.assertTrue(res["run_id"])
        self.assertEqual(res["format"], "json")
        mock_file_handle.assert_called_once()