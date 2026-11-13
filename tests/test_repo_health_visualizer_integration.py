import unittest
import os
import shutil
import uuid
import random
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"./test_viz_output_{uuid.uuid4()}"
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_pipeline_visualization_integration(self):
        random_repo_path = f"/mock/repo/path_{uuid.uuid4()}"
        specific_run_id = str(uuid.uuid4())
        formats = ["json", "png", "svg", "html", "unknown_ext"]
        chosen_format = random.choice(formats)

        diagnostic_result = self.diagnostic.run_diagnostics(
            repo_path=random_repo_path,
            run_id=specific_run_id
        )

        self.assertEqual(diagnostic_result["run_id"], specific_run_id)
        self.assertEqual(diagnostic_result["repo_path"], random_repo_path)
        self.assertIn("metrics", diagnostic_result)

        prediction_result = self.predictor.execute_pipeline(
            diagnostic_data=diagnostic_result,
            seed=random.randint(1, 1000)
        )

        self.assertEqual(prediction_result["run_id"], specific_run_id)
        self.assertIn("prediction", prediction_result)

        visualization_result = self.visualizer.generate_visualization(
            prediction_data=prediction_result,
            output_format=chosen_format,
            target_directory=self.test_dir,
            run_identifier=specific_run_id
        )

        expected_ext = chosen_format if chosen_format in ["png", "svg", "json", "html"] else "json"
        expected_filename = f"visualization_{specific_run_id}.{expected_ext}"
        expected_file_path = os.path.join(self.test_dir, expected_filename)

        self.assertEqual(visualization_result["run_id"], specific_run_id)
        self.assertEqual(visualization_result["format"], expected_ext)
        self.assertEqual(visualization_result["file_path"], expected_file_path)

        self.assertTrue(os.path.exists(expected_file_path), "Ф