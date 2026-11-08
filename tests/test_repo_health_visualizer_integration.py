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
        self.test_dir = f"test_output_{uuid.uuid4()}"
        self.repo_path = f"/mock/repo/{uuid.uuid4()}"
        self.run_id = str(uuid.uuid4())
        self.seed_val = random.randint(1, 1000)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_diagnostic_prediction_visualization_pipeline(self):
        diagnostic_module = RepoHealthDiagnostic()
        diagnostic_result = diagnostic_module.run_diagnostics(
            repo_path=self.repo_path,
            run_id=self.run_id
        )

        self.assertEqual(diagnostic_result["run_id"], self.run_id)
        self.assertEqual(diagnostic_result["repo_path"], self.repo_path)
        self.assertIn("metrics", diagnostic_result)

        predictor_pipeline = RepoHealthPredictorPipeline()
        prediction_result = predictor_pipeline.execute_pipeline(
            diagnostic_data=diagnostic_result,
            seed=self.seed_val
        )

        self.assertEqual(prediction_result["run_id"], self.run_id)
        self.assertEqual(prediction_result["seed"], self.seed_val)
        self.assertIn("prediction", prediction_result)

        visualizer = RepoHealthVisualizer()
        formats = ["json", "html", "svg", "png", "invalid_format"]
        chosen_format = random.choice(formats)

        vis_result = visualizer.generate_visualization(
            prediction_data=prediction_result,
            output_format=chosen_format,
            target_directory=self.test_dir,
            run_identifier=self.run_id
        )

        expected_ext = chosen_format.lower()
        if expected_ext not in ["png", "svg", "json", "html"]:
            expected_ext = "json"

        self.assertEqual(vis_result["run_id"], self.run_id)
        self.assertEqual(vis_result["format"], expected_ext)
        
        expected_file_name = f"visualization_{self.run_id}.{expected_ext}"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        
        self.assertEqual(vis_result["file_path"], expected_file_path)
        self.assertTrue(os.path.exists(expected_file_path), "Файл визуализации не был создан на диске")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(self.run_id, file_content)
        self.assertIn(self.repo_path, file_content)

if __name__ == "__main__":
    unittest.main()