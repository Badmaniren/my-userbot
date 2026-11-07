import unittest
import uuid
import random
import tempfile
import pathlib
import os

from skills.repo_health_export_hub import (
    RepoHealthExportHub,
)
from skills.repo_health_diagnostic import (
    RepoHealthDiagnostic,
)
from skills.repo_health_predictor_pipeline import (
    RepoHealthPredictorPipeline,
)


class TestRepoHealthExportHubIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        
        self.export_hub = RepoHealthExportHub()
        self.diagnostic_skill = RepoHealthDiagnostic()
        self.predictor_skill = RepoHealthPredictorPipeline()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_health_and_predictions_real_flow(self):
        random_project_id = str(uuid.uuid4())
        random_metric_value = round(random.uniform(10.0, 99.9), 2)
        
        diagnostic_data = self.diagnostic_skill.execute(
            repo_path=self.repo_path,
            project_id=random_project_id,
            base_score=random_metric_value
        )
        
        prediction_data = self.predictor_skill.execute(
            diagnostic_report=diagnostic_data,
            horizon_days=random.randint(7, 90)
        )

        formats = ["json", "csv", "markdown"]
        chosen_format = random.choice(formats)
        
        export_result = self.export_hub.execute(
            diagnostic_data=diagnostic_data,
            prediction_data=prediction_data,
            export_format=chosen_format,
            target_directory=self.repo_path
        )

        self.assertIn("status", export_result)
        self.assertEqual(export_result["status"], "success")
        self.assertIn("file_path", export_result)
        
        output_file = pathlib.Path(export_result["file_path"])
        self.assertTrue(output_file.exists(), f"Exported file {output_file} was not created on disk.")
        
        file_content = output_file.read_text(encoding="utf-8")
        self.assertIn(random_project_id, file_content, "Random project ID must be present in the exported report.")

    def test_export_unsupported_format_raises_error(self):
        invalid_format = f"invalid_{uuid.uuid4().hex[:6]}"
        
        with self.assertRaises((ValueError, KeyError, Exception)):
            self.export_hub.execute(
                diagnostic_data={"id": str(uuid.uuid4())},
                prediction_data={"trend": "stable"},
                export_format=invalid_format,
                target_directory=self.repo_path
            )


if __name__ == "__main__":
    unittest.main()