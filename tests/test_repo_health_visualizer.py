import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import json
import tempfile
import shutil

from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerStrict(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_health_diagnostic_run_and_analyze_random(self):
        random_repo_path = f"/path/to/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        random_run_id = uuid.uuid4().hex

        diag_result = self.diagnostic.run_diagnostics(random_repo_path, random_run_id)
        
        self.assertEqual(diag_result["run_id"], random_run_id)
        self.assertEqual(diag_result["repo_path"], random_repo_path)
        self.assertIn("metrics", diag_result)
        self.assertIn("health_score", diag_result["metrics"])
        self.assertIn("complexity", diag_result["metrics"])
        self.assertIn("issues", diag_result["metrics"])

        analyze_result = self.diagnostic.analyze(random_repo_path, random_run_id)
        self.assertEqual(analyze_result["run_id"], random_run_id)
        self.assertEqual(analyze_result["repo_path"], random_repo_path)

    def test_repo_health_diagnostic_default_run_id(self):
        random_repo_path = f"/opt/{uuid.uuid4().hex}"
        diag_result = self.diagnostic.run_diagnostics(random_repo_path)
        
        self.assertIsNotNone(diag_result["run_id"])
        self.assertEqual(diag_result["repo_path"], random_repo_path)

    def test_repo_health_predictor_pipeline_execution(self):
        random_run_id = uuid.uuid4().hex
        random_repo_path = f"/home/user/{uuid.uuid4().hex}"
        random_seed = random.randint(1, 1000)

        diagnostic_data = {
            "run_id": random_run_id,
            "repo_path": random_repo_path,
            "metrics": {
                "health_score": random.random(),
                "complexity": random.randint(1, 50),
                "issues": random.randint(0, 5)
            }
        }

        prediction_result = self.predictor.execute_pipeline(diagnostic_data, seed=random_seed)

        self.assertEqual(prediction_result["run_id"], random_run_id)
        self.assertEqual(prediction_result["seed"], random_seed)
        self.assertEqual(prediction_result["diagnostic_data"], diagnostic_data)
        self.assertIn("prediction", prediction_result)
        self.assertIn("risk_level", prediction_result["prediction"])
        self.assertIn("score", prediction_result["prediction"])
        self.assertIn(prediction_result["prediction"]["risk_level"], ["LOW", "HIGH"])

    def test_repo_health_visualizer_generation_formats(self):
        random_run_id = uuid.uuid4().hex
        random_repo_path = f"/var/git/{uuid.uuid4().hex}"
        random_score = random.random()
        
        prediction_data = {
            "run_id": random_run_id,
            "diagnostic_data": {
                "repo_path": random_repo_path,
                "run_id": random_run_id
            },
            "prediction": {
                "risk_level": random.choice(["LOW", "HIGH"]),
                "score": random_score
            }
        }

        allowed_formats = ["png", "svg", "json", "html"]
        chosen_format = random.choice(allowed_formats)

        res = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=chosen_format,
            target_directory=self.test_dir,
            run_identifier=random_run_id
        )

        self.assertEqual(res["format"], chosen_format)
        self.assertEqual(res["run_id"], random_run_id)
        self.assertTrue(os.path.exists(res["file_path"]))

        with open(res["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(random_run_id, content)
            self.assertIn(random_repo_path, content)

    def test_repo_health_visualizer_fallback_format(self):
        random_run_id = uuid.uuid4().hex
        invalid_format = uuid.uuid4().hex[:5]

        prediction_data = {
            "run_id": random_run_id,
            "diagnostic_data": {"repo_path": f"/tmp/{uuid.uuid4().hex}"}
        }

        res = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=invalid_format,
            target_directory=self.test_dir
        )

        self.assertEqual(res["format"], "json")
        self.assertTrue(res["file_path"].endswith(f"visualization_{random_run_id}.json"))
        self.assertTrue(os.path.exists(res["file_path"]))

    def test_repo_health_visualizer_mocked_file_write(self):
        random_run_id = uuid.uuid4().hex
        random_repo_path = f"/srv/repo/{uuid.uuid4().hex}"
        
        prediction_data = {
            "run_id": random_run_id,
            "diagnostic_data": {"repo_path": random_repo_path}
        }

        mock_file_instance = mock_open().return_value

        with patch("builtins.open", mock_file_instance) as mocked_file, \
             patch("os.makedirs") as mocked_makedirs:
            
            res = self.visualizer.generate_visualization(
                prediction_data=prediction_data,
                output_format="svg",
                target_directory=self.test_dir,
                run_identifier=random_run_id
            )

            mocked_makedirs.assert_called_once_with(self.test_dir, exist_ok=True)
            mocked_file.assert_called_once()
            
            written_content = "".join(call.args[0] for call in mock_file_instance.write.call_args_list)
            self.assertIn(random_run_id, written_content)
            self.assertIn(random_repo_path, written_content)
            self.assertEqual(res["run_id"], random_run_id)
            self.assertEqual(res["format"], "svg")

if __name__ == "__main__":
    unittest.main()