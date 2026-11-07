import unittest
import os
import uuid
import random
import tempfile
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_repo_health_pipeline_integration(self):
        random_repo_path = f"/tmp/repo_{uuid.uuid4()}"
        random_run_id = str(uuid.uuid4())
        random_seed = random.randint(1, 1000)
        output_format = random.choice(["json", "html", "svg", "png"])

        diagnostic_result = self.diagnostic.run_diagnostics(
            repo_path=random_repo_path,
            run_id=random_run_id
        )

        self.assertEqual(diagnostic_result["run_id"], random_run_id)
        self.assertEqual(diagnostic_result["repo_path"], random_repo_path)
        self.assertIn("metrics", diagnostic_result)

        prediction_result = self.predictor.execute_pipeline(
            diagnostic_data=diagnostic_result,
            seed=random_seed
        )

        self.assertEqual(prediction_result["run_id"], random_run_id)
        self.assertEqual(prediction_result["seed"], random_seed)
        self.assertIn("prediction", prediction_result)

        visualization_result = self.visualizer.generate_visualization(
            prediction_data=prediction_result,
            output_format=output_format,
            target_directory=self.test_dir.name,
            run_identifier=random_run_id
        )

        expected_filename = f"visualization_{random_run_id}.{output_format}"
        expected_filepath = os.path.join(self.test_dir.name, expected_filename)

        self.assertEqual(visualization_result["file_path"], expected_filepath)
        self.assertEqual(visualization_result["format"], output_format)
        self.assertEqual(visualization_result["run_id"], random_run_id)

        self.assertTrue(os.path.exists(expected_filepath))

        with open(expected_filepath, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(random_run_id, file_content)
        self.assertIn(random_repo_path, file_content)

if __name__ == "__main__":
    unittest.main()