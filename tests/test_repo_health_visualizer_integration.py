import unittest
import os
import uuid
import random
import tempfile
from skills.repo_health_visualizer import RepoHealthDiagnostic, RepoHealthPredictorPipeline, RepoHealthVisualizer

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def test_end_to_end_visualization_pipeline(self):
        diagnostic = RepoHealthDiagnostic()
        predictor = RepoHealthPredictorPipeline()
        visualizer = RepoHealthVisualizer()

        random_repo_name = f"test_repo_{uuid.uuid4().hex[:8]}"
        random_run_id = str(uuid.uuid4())
        random_seed = random.randint(1, 1000)
        output_formats = ["json", "svg", "html", "png"]
        chosen_format = random.choice(output_formats)

        with tempfile.TemporaryDirectory() as temp_dir:
            diag_result = diagnostic.run_diagnostics(repo_path=random_repo_name, run_id=random_run_id)
            
            self.assertEqual(diag_result["run_id"], random_run_id)
            self.assertEqual(diag_result["repo_path"], random_repo_name)
            self.assertIn("metrics", diag_result)

            pipeline_result = predictor.execute_pipeline(diagnostic_data=diag_result, seed=random_seed)

            self.assertEqual(pipeline_result["run_id"], random_run_id)
            self.assertEqual(pipeline_result["seed"], random_seed)
            self.assertIn("prediction", pipeline_result)

            viz_result = visualizer.generate_visualization(
                prediction_data=pipeline_result,
                output_format=chosen_format,
                target_directory=temp_dir,
                run_identifier=random_run_id
            )

            self.assertEqual(viz_result["run_id"], random_run_id)
            self.assertEqual(viz_result["format"], chosen_format)
            
            expected_file_path = viz_result["file_path"]
            self.assertTrue(os.path.exists(expected_file_path), f"Visualization file should exist at {expected_file_path}")

            with open(expected_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            self.assertIn(random_run_id, file_content)
            self.assertIn(random_repo_name, file_content)

if __name__ == "__main__":
    unittest.main()