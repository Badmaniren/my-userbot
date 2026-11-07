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
        self.test_dir = "."

    def tearDown(self):
        for ext in ["json", "png", "svg", "html"]:
            file_path = os.path.join(self.test_dir, f"visualization_{self.run_id}.{ext}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_repo_health_visualizer_pipeline_integration(self):
        self.run_id = str(uuid.uuid4())
        random_repo_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        seed_value = random.randint(1, 1000)
        output_format = random.choice(["json", "png", "svg", "html"])

        diag_result = self.diagnostic.run_diagnostics(repo_path=random_repo_path, run_id=self.run_id)
        
        self.assertEqual(diag_result["run_id"], self.run_id)
        self.assertEqual(diag_result["repo_path"], random_repo_path)
        self.assertIn("metrics", diag_result)

        pred_result = self.predictor.execute_pipeline(diagnostic_data=diag_result, seed=seed_value)

        self.assertEqual(pred_result["run_id"], self.run_id)
        self.assertEqual(pred_result["seed"], seed_value)
        self.assertIn("prediction", pred_result)

        vis_result = self.visualizer.generate_visualization(
            prediction_data=pred_result,
            output_format=output_format,
            target_directory=self.test_dir,
            run_identifier=self.run_id
        )

        self.assertEqual(vis_result["run_id"], self.run_id)
        self.assertEqual(vis_result["format"], output_format)
        
        expected_file_path = vis_result["file_path"]
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.run_id, content)
        self.assertIn(random_repo_path, content)

if __name__ == "__main__":
    unittest.main()