import json
import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.anomaly_logger import AnomalyLogger
from skills.report_exporter import ReportExporter, ReportExporterError, export_report


class TestReportExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="exporter_test_")
        self.logger_file = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.log")
        self.anomaly_logger = AnomalyLogger(self.logger_file)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_end_to_end_anomaly_logging_and_json_export(self):
        unique_source = f"service_{uuid.uuid4().hex[:8]}"
        unique_token = uuid.uuid4().hex
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_metric_val = random.randint(100, 9999)

        details = {"error_token": unique_token, "code": random_metric_val}
        telemetry = {"cpu_load": round(random.uniform(10.5, 99.5), 2)}

        self.anomaly_logger.log_anomaly(
            source=unique_source,
            severity=random_severity,
            details=details,
            telemetry_snapshot=telemetry
        )

        structured_data = self.anomaly_logger.get_structured_report()
        if not isinstance(structured_data, dict):
            structured_data = {"audit_report": structured_data}

        random_report_id = f"rep_{uuid.uuid4().hex}"
        structured_data["report_id"] = random_report_id

        output_file = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex}.json")

        export_report(structured_data, output_file, format_type="json")

        self.assertTrue(os.path.isfile(output_file), "Exported JSON file must exist on disk.")

        with open(output_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data.get("report_id"), random_report_id)
        raw_exported = json.dumps(loaded_data)
        self.assertIn(unique_source, raw_exported)
        self.assertIn(unique_token, raw_exported)
        self.assertIn(str(random_metric_val), raw_exported)

    def test_text_export_integration_with_anomaly_logger(self):
        unique_source = f"detector_{uuid.uuid4().hex[:8]}"
        marker_text = f"marker_{uuid.uuid4().hex}"
        self.anomaly_logger.log_anomaly(
            source=unique_source,
            severity="WARNING",
            details={"diagnostic": marker_text},
            telemetry_snapshot={"mem_mb": random.randint(512, 4096)}
        )

        raw_report = self.anomaly_logger.get_structured_report()
        report_data = raw_report if isinstance(raw_report, dict) else {"report": raw_report}
        unique_report_id = f"txt_rep_{uuid.uuid4().hex}"
        report_data["report_id"] = unique_report_id

        exporter = ReportExporter(report_data)
        text_output = exporter.export_text()

        self.assertIn(unique_report_id, text_output)
        self.assertIn(unique_source, text_output)
        self.assertIn(marker_text, text_output)

        output_text_file = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.txt")
        export_report(report_data, output_text_file, format_type="text")

        self.assertTrue(os.path.isfile(output_text_file))
        with open(output_text_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertEqual(file_content, text_output)

    def test_serialize_and_custom_formatting(self):
        random_id = str(uuid.uuid4())
        random_status = f"status_{uuid.uuid4().hex[:6]}"
        data = {
            "report_id": random_id,
            "status": random_status
        }
        exporter = ReportExporter(data)

        self.assertEqual(exporter.report_id, random_id)
        serialized_json = exporter.serialize()
        self.assertEqual(serialized_json, exporter.export_json())

        template = "Report [{report_id}] finished with status: {status}"
        custom_formatted = exporter.export_custom_text(template)
        status = random_status
        expected_text = f"Report [{random_id}] finished with status: {status}"
        self.assertEqual(custom_formatted, expected_text)

    def test_validation_and_unsupported_formats(self):
        with self.assertRaises(ReportExporterError):
            ReportExporter(["invalid_data_list"])

        with self.assertRaises(ReportExporterError):
            ReportExporter(12345)

        valid_data = {"report_id": str(uuid.uuid4())}
        exporter = ReportExporter(valid_data)

        with self.assertRaises(ReportExporterError):
            exporter.export_custom_text("Missing key: {non_existent_key}")

        dummy_path = os.path.join(self.test_dir, "unsupported.bin")
        with self.assertRaises(ReportExporterError):
            export_report(valid_data, dummy_path, format_type="unsupported_fmt")


if __name__ == "__main__":
    unittest.main()