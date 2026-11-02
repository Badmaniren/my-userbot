import unittest
import os
import uuid
import random
import tempfile
from skills.patch_reporter import PatchReporter, PatchReporterError

class TestPatchReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.reporter = PatchReporter()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_report_generation_and_export_pipeline(self):
        unique_patch_id = f"patch-{uuid.uuid4().hex[:8]}"
        random_score = round(random.uniform(0.0, 1.0), 2)
        random_metric = random.randint(100, 999)

        analysis_data = {
            "patch_id": unique_patch_id,
            "complexity": "medium",
            "files_changed": random.randint(1, 10)
        }

        risk_data = {
            "score": random_score,
            "risk_level": "HIGH" if random_score >= 0.7 else "LOW",
            "factors": [f"factor_{uuid.uuid4().hex[:4]}"]
        }

        verification_data = {
            "status": "PASSED" if random_score < 0.7 else "FAILED",
            "checks": [f"check_{random_metric}"]
        }

        metadata = {
            "author": f"user_{uuid.uuid4().hex[:6]}"
        }

        report = self.reporter.generate_report(
            analysis_data=analysis_data,
            risk_data=risk_data,
            verification_data=verification_data,
            metadata=metadata
        )

        self.assertIn("report_id", report)
        self.assertEqual(report["patch_id"], unique_patch_id)
        self.assertEqual(report["analysis"], analysis_data)
        self.assertEqual(report["risks"], risk_data)
        self.assertEqual(report["verification"], verification_data)
        self.assertEqual(report["metadata"], metadata)

        json_output = self.reporter.export_json(report)
        self.assertIsInstance(json_output, str)
        self.assertIn(unique_patch_id, json_output)

        file_name = f"report_{uuid.uuid4().hex}.json"
        output_json_path = os.path.join(self.test_dir.name, file_name)
        exported_path = self.reporter.export_json(report, output_path=output_json_path)

        self.assertEqual(exported_path, output_json_path)
        self.assertTrue(os.path.exists(output_json_path))

        with open(output_json_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(unique_patch_id, file_content)

        md_file_name = f"report_{uuid.uuid4().hex}.md"
        output_md_path = os.path.join(self.test_dir.name, md_file_name)
        exported_md_path = self.reporter.export_markdown(report, output_path=output_md_path)

        self.assertEqual(exported_md_path, output_md_path)
        self.assertTrue(os.path.exists(output_md_path))

        with open(output_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn(unique_patch_id, md_content)
            self.assertIn("Summary", md_content)
            self.assertIn("Analysis", md_content)
            self.assertIn("Risks", md_content)

    def test_invalid_data_handling(self):
        with self.assertRaises(PatchReporterError):
            self.reporter.generate_report(
                analysis_data=None,
                risk_data={"score": 0.1}
            )

        with self.assertRaises(PatchReporterError):
            self.reporter.generate_report(
                analysis_data={"patch_id": "123"},
                risk_data="not_a_dict"
            )

if __name__ == "__main__":
    unittest.main()