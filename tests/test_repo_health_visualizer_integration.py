import unittest
import os
import uuid
import random
from skills.repo_health_visualizer import (
    RepoHealthDiagnostic,
    RepoHealthPredictorPipeline,
    RepoHealthVisualizer
)

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()
        self.visualizer = RepoHealthVisualizer()
        self.test_dir = f"./test_artifacts_{uuid.uuid4()}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.test_dir)

    def test_full_pipeline_visualization_integration(self):
        random_repo_path = f"/mock/repo/path_{uuid.uuid4()}"
        random_run_id = str(uuid.uuid4())
        random_seed = random.randint(1, 10000)
        output_formats = ["json", "svg", "html", "png"]
        selected_format = random.choice(output_formats)

        diagnostic_result = self.diagnostic.run_diagnostics(
            repo_path=random_repo_path,
            run_id=random_run_id
        )

        self.assertEqual(diagnostic_result.get("run_id"), random_run_id)
        self.assertEqual(diagnostic_result.get("repo_path"), random_repo_path)
        self.assertIn("metrics", diagnostic_result)

        prediction_result = self.predictor.execute_pipeline(
            diagnostic_data=diagnostic_result,
            seed=random_seed
        )

        self.assertEqual(prediction_result.get("run_id"), random_run_id)
        self.assertEqual(prediction_result.get("seed"), random_seed)
        self.assertIn("prediction", prediction_result)

        visualization_result = self.visualizer.generate_visualization(
            prediction_data=prediction_result,
            output_format=selected_format,
            target_directory=self.test_dir,
            run_identifier=random_run_id
        )

        returned_file_path = visualization_result.get("file_path")
        returned_format = visualization_result.get("format")
        returned_run_id = visualization_result.get("run_id")

        self.assertEqual(returned_run_id, random_run_id)
        self.assertEqual(returned_format, selected_format)
        self.assertTrue(os.path.exists(returned_file_path))

        with open(returned_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(random_run_id, file_content)
        self.assertIn(random_repo_path, file_content)

if __name__ == "__main__":
    unittest.main()