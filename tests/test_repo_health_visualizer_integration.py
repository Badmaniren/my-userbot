import unittest
import os
import uuid
import random
from skills.repo_health_visualizer import RepoHealthDiagnostic, RepoHealthPredictorPipeline, RepoHealthVisualizer

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.test_dir = f"./test_artifacts_{uuid.uuid4()}"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.test_dir)

    def test_repo_health_visualizer_pipeline_integration(self):
        random_repo_path = f"/path/to/virtual/repo_{uuid.uuid4()}"
        random_run_id = str(uuid.uuid4())
        random_seed = random.randint(1, 1000)
        output_format = random.choice(["png", "svg", "json", "html"])

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
            target_directory=self.test_dir,
            run_identifier=random_run_id
        )

        expected_file_name = f"visualization_{random_run_id}.{output_format}"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)

        self.assertEqual(visualization_result["run_id"], random_run_id)
        self.assertEqual(visualization_result["format"], output_format)
        self.assertEqual(visualization_result["file_path"], expected_file_path)
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(random_run_id, content)
            self.assertIn(random_repo_path, content)

if __name__ == "__main__":
    unittest.main()