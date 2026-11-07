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

    def test_repo_health_visualization_pipeline_integration(self):
        random_repo_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        specific_run_id = str(uuid.uuid4())
        seed_value = random.randint(1, 1000)
        
        supported_formats = ["png", "svg", "json", "html"]
        chosen_format = random.choice(supported_formats)

        diagnostic_result = self.diagnostic.run_diagnostics(
            repo_path=random_repo_path,
            run_id=specific_run_id
        )
        
        self.assertEqual(diagnostic_result["run_id"], specific_run_id)
        self.assertEqual(diagnostic_result["repo_path"], random_repo_path)
        self.assertIn("metrics", diagnostic_result)

        prediction_result = self.predictor.execute_pipeline(
            diagnostic_data=diagnostic_result,
            seed=seed_value
        )
        
        self.assertEqual(prediction_result["run_id"], specific_run_id)
        self.assertEqual(prediction_result["seed"], seed_value)
        self.assertIn("prediction", prediction_result)

        visualization_result = self.visualizer.generate_visualization(
            prediction_data=prediction_result,
            output_format=chosen_format,
            target_directory=self.test_dir.name,
            run_identifier=specific_run_id
        )

        self.assertEqual(visualization_result["run_id"], specific_run_id)
        self.assertEqual(visualization_result["format"], chosen_format)
        
        expected_file_name = f"visualization_{specific_run_id}.{chosen_format}"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        
        self.assertEqual(visualization_result["file_path"], expected_file_path)
        self.assertTrue(os.path.exists(expected_file_path), f"File {expected_file_path} was not created by visualizer.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(specific_run_id, file_content)
        self.assertIn(random_repo_path, file_content)

if __name__ == "__main__":
    unittest.main()