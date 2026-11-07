import unittest
import uuid
import random
import os
import tempfile
from skills.repo_health_visualizer import RepoHealthVisualizer
from skills.repo_health_diagnostic import RepoHealthDiagnostic
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.visualizer = RepoHealthVisualizer()
        self.diagnostic = RepoHealthDiagnostic()
        self.predictor = RepoHealthPredictorPipeline()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_health_visualizer_end_to_end_integration(self):
        random_seed_val = random.randint(1000, 9999)
        unique_run_id = str(uuid.uuid4())
        
        dummy_file_name = f"metric_{unique_run_id}.log"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        with open(dummy_file_path, "w") as f:
            f.write(f"RUN_ID: {unique_run_id}\nSEED: {random_seed_val}\nHEALTH_SCORE: {random.random()}")

        diagnostic_data = self.diagnostic.run_diagnostics(self.repo_path, run_id=unique_run_id)
        prediction_data = self.predictor.execute_pipeline(diagnostic_data, seed=random_seed_val)
        
        output_format = random.choice(["png", "svg", "json", "html"])
        visualization_result = self.visualizer.generate_visualization(
            prediction_data=prediction_data,
            output_format=output_format,
            target_directory=self.repo_path,
            run_identifier=unique_run_id
        )

        self.assertIsNotNone(visualization_result)
        self.assertIn("file_path", visualization_result)
        
        generated_file = visualization_result["file_path"]
        self.assertTrue(os.path.exists(generated_file), f"Visualized artifact was not created at {generated_file}")
        
        with open(generated_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            self.assertIn(unique_run_id, content, "Generated visualization does not contain the unique run ID reference")

if __name__ == "__main__":
    unittest.main()