import unittest
import os
import uuid
import random
from skills.repo_health_visualizer import RepoHealthDiagnostic, RepoHealthPredictorPipeline, RepoHealthVisualizer

class TestRepoHealthVisualizerIntegration(unittest.TestCase):
    def test_full_health_pipeline_integration(self):
        diagnostic_skill = RepoHealthDiagnostic()
        predictor_skill = RepoHealthPredictorPipeline()
        visualizer_skill = RepoHealthVisualizer()

        random_repo_name = f"test_repo_{uuid.uuid4().hex[:8]}"
        random_run_id = str(uuid.uuid4())
        random_seed = random.randint(1, 1000)
        target_dir = f"./temp_viz_dir_{uuid.uuid4().hex[:8]}"
        output_format = "html"

        try:
            diagnostic_result = diagnostic_skill.run_diagnostics(
                repo_path=random_repo_name,
                run_id=random_run_id
            )

            self.assertEqual(diagnostic_result["run_id"], random_run_id)
            self.assertEqual(diagnostic_result["repo_path"], random_repo_name)
            self.assertIn("metrics", diagnostic_result)

            prediction_result = predictor_skill.execute_pipeline(
                diagnostic_data=diagnostic_result,
                seed=random_seed
            )

            self.assertEqual(prediction_result["run_id"], random_run_id)
            self.assertEqual(prediction_result["seed"], random_seed)
            self.assertIn("prediction", prediction_result)

            visualization_result = visualizer_skill.generate_visualization(
                prediction_data=prediction_result,
                output_format=output_format,
                target_directory=target_dir,
                run_identifier=random_run_id
            )

            generated_file_path = visualization_result.get("file_path")
            self.assertEqual(visualization_result["run_id"], random_run_id)
            self.assertEqual(visualization_result["format"], output_format)
            self.assertTrue(os.path.exists(generated_file_path), "Файл визуализации не был создан на диске.")

            with open(generated_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            self.assertIn(random_run_id, file_content)
            self.assertIn(random_repo_name, file_content)

        finally:
            if os.path.exists(target_dir):
                for file_name in os.listdir(target_dir):
                    file_path = os.path.join(target_dir, file_name)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(target_dir)

if __name__ == "__main__":
    unittest.main()