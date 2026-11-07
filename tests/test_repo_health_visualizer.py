import os
import unittest
import uuid
import random
import json
from unittest.mock import patch
import tempfile

from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerInquisitorial(unittest.TestCase):
    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.pipeline = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_repo_health_diagnostic_run(self):
        random_repo = f"/path/to/{uuid.uuid4().hex}"
        random_run_id = uuid.uuid4().hex

        result = self.diagnostic.run_diagnostics(random_repo, random_run_id)

        self.assertEqual(result["run_id"], random_run_id)
        self.assertEqual(result["repo_path"], random_repo)
        self.assertIn("metrics", result)
        self.assertIn("health_score", result["metrics"])
        self.assertIn("complexity", result["metrics"])
        self.assertIn("issues", result["metrics"])

    def test_repo_health_diagnostic_analyze_backward_compatibility(self):
        random_repo = f"/repo/{uuid.uuid4().hex}"
        result = self.diagnostic.analyze(random_repo)
        self.assertIn("run_id", result)
        self.assertEqual(result["repo_path"], random_repo)

    def test_repo_health_predictor_pipeline_execution(self):
        random_repo = f"/var/repo/{uuid.uuid4().hex}"
        random_run_id = uuid.uuid4().hex
        diagnostic_data = self.diagnostic.run_diagnostics(random_repo, random_run_id)
        
        random_seed = random.randint(1, 1000)
        pipeline_result = self.pipeline.execute_pipeline(diagnostic_data, seed=random_seed)

        self.assertEqual(pipeline_result["run_id"], random_run_id)
        self.assertEqual(pipeline_result["seed"], random_seed)
        self.assertIn("prediction", pipeline_result)
        self.assertIn("risk_level", pipeline_result["prediction"])
        self.assertIn(pipeline_result["prediction"]["risk_level"], ["LOW", "HIGH"])

    def test_repo_health_visualizer_generation_formats(self):
        random_repo = f"/srv/git/{uuid.uuid4().hex}"
        random_run_id = uuid.uuid4().hex
        diagnostic_data = self.diagnostic.run_diagnostics(random_repo, random_run_id)
        prediction_data = self.pipeline.execute_pipeline(diagnostic_data)

        supported_formats = ["png", "svg", "json", "html"]
        chosen_format = random.choice(supported_formats)

        result = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=chosen_format,
            target_directory=self.temp_dir.name,
            run_identifier=random_run_id
        )

        self.assertEqual(result["run_id"], random_run_id)
        self.assertEqual(result["format"], chosen_format)
        self.assertTrue(os.path.exists(result["file_path"]))
        
        with open(result["file_path"], "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(random_run_id, file_content)
            self.assertIn(random_repo, file_content)

    def test_repo_health_visualizer_fallback_format(self):
        random_repo = f"/opt/{uuid.uuid4().hex}"
        diagnostic_data = self.diagnostic.run_diagnostics(random_repo)
        prediction_data = self.pipeline.execute_pipeline(diagnostic_data)

        invalid_format = uuid.uuid4().hex[:5]

        result = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=invalid_format,
            target_directory=self.temp_dir.name
        )

        self.assertEqual(result["format"], "json")
        self.assertTrue(result["file_path"].endswith(".json"))
        self.assertTrue(os.path.exists(result["file_path"]))

    def test_repo_health_visualizer_mocked_file_writing(self):
        random_repo = f"/home/user/{uuid.uuid4().hex}"
        random_run_id = uuid.uuid4().hex
        diagnostic_data = self.diagnostic.run_diagnostics(random_repo, random_run_id)
        prediction_data = self.pipeline.execute_pipeline(diagnostic_data)

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = self.visualizer.generate_visualization(
                prediction_data=prediction_data,
                output_format="svg",
                target_directory="/fake/dir",
                run_identifier=random_run_id
            )

            mock_file.assert_called_once()
            self.assertEqual(result["format"], "svg")
            self.assertEqual(result["run_id"], random_run_id)

if __name__ == "__main__":
    unittest.main()