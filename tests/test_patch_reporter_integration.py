import json
import os
import random
import tempfile
import unittest
import uuid

from skills.anomaly_logger import AnomalyLogger
from skills.patch_reporter import PatchReporter


class TestPatchReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.anomaly_log_path = os.path.join(
            self.temp_dir.name, f"anomalies_{uuid.uuid4().hex}.json"
        )
        self.anomaly_logger = AnomalyLogger(log_path=self.anomaly_log_path)
        self.reporter = PatchReporter()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_and_export_report_with_anomalies(self):
        patch_id = f"patch-{uuid.uuid4().hex[:12]}"
        random_token = uuid.uuid4().hex
        source_component = f"core_module_{uuid.uuid4().hex[:6]}"

        lines_added = random.randint(10, 500)
        lines_removed = random.randint(1, 200)
        risk_score = round(random.uniform(0.05, 0.95), 3)

        analysis_data = {
            "token": random_token,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "changed_files": [f"src/{uuid.uuid4().hex[:8]}.py", "README.md"],
        }
        risk_assessment = {
            "score": risk_score,
            "level": "HIGH" if risk_score > 0.5 else "LOW",
            "flags": [f"flag_{uuid.uuid4().hex[:6]}"],
        }
        verification_results = {
            "status": "PASSED",
            "passed_tests": random.randint(5, 50),
            "failed_tests": 0,
        }

        # Интеграция: логируем реальную аномалию через AnomalyLogger
        anomaly_detail_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.anomaly_logger.log_anomaly(
            source=source_component,
            severity="warning",
            details={anomaly_detail_key: random_token},
            telemetry_snapshot={"cpu_load": random.uniform(10.0, 90.0)},
        )
        anomalies = self.anomaly_logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)

        # Генерация структурированного отчета
        report = self.reporter.generate_report(
            patch_id=patch_id,
            analysis=analysis_data,
            risk_assessment=risk_assessment,
            verification_results=verification_results,
            anomalies=anomalies,
        )

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("patch_id"), patch_id)
        self.assertIn("analysis", report)
        self.assertIn("risk_assessment", report)
        self.assertIn("verification_results", report)
        self.assertIn("anomalies", report)

        # Экспорт в JSON
        json_output_path = os.path.join(
            self.temp_dir.name, f"report_{uuid.uuid4().hex}.json"
        )
        exported_json_path = self.reporter.export_json(report, json_output_path)

        self.assertTrue(os.path.exists(exported_json_path))
        with open(exported_json_path, "r", encoding="utf-8") as f:
            loaded_json = json.load(f)

        self.assertEqual(loaded_json["patch_id"], patch_id)
        self.assertEqual(loaded_json["analysis"]["token"], random_token)
        self.assertEqual(loaded_json["analysis"]["lines_added"], lines_added)
        self.assertEqual(loaded_json["risk_assessment"]["score"], risk_score)
        self.assertEqual(len(loaded_json["anomalies"]), 1)
        self.assertEqual(
            loaded_json["anomalies"][0]["details"][anomaly_detail_key], random_token
        )

        # Экспорт в Markdown
        md_output_path = os.path.join(
            self.temp_dir.name, f"report_{uuid.uuid4().hex}.md"
        )
        exported_md_path = self.reporter.export_markdown(report, md_output_path)

        self.assertTrue(os.path.exists(exported_md_path))
        with open(exported_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn(patch_id, md_content)
        self.assertIn(random_token, md_content)
        self.assertIn(str(lines_added), md_content)
        self.assertIn(source_component, md_content)
        self.assertTrue(md_content.startswith("#") or "# " in md_content)

    def test_generate_report_minimal_and_exports(self):
        patch_id = f"patch-{uuid.uuid4().hex}"
        unique_file = f"module_{uuid.uuid4().hex[:6]}.py"

        analysis_data = {"changed_files": [unique_file]}
        risk_assessment = {"level": "LOW", "score": 0.0}
        verification_results = {"status": "SUCCESS"}

        report = self.reporter.generate_report(
            patch_id=patch_id,
            analysis=analysis_data,
            risk_assessment=risk_assessment,
            verification_results=verification_results,
        )

        json_output_path = os.path.join(
            self.temp_dir.name, f"summary_{uuid.uuid4().hex}.json"
        )
        md_output_path = os.path.join(
            self.temp_dir.name, f"summary_{uuid.uuid4().hex}.md"
        )

        self.reporter.export_json(report, json_output_path)
        self.reporter.export_markdown(report, md_output_path)

        self.assertTrue(os.path.exists(json_output_path))
        self.assertTrue(os.path.exists(md_output_path))

        with open(json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn(unique_file, data["analysis"]["changed_files"])

        with open(md_output_path, "r", encoding="utf-8") as f:
            md_text = f.read()
            self.assertIn(patch_id, md_text)
            self.assertIn(unique_file, md_text)


if __name__ == "__main__":
    unittest.main()