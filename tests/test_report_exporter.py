import json
import os
import random
import string
import tempfile
import unittest
import uuid
from unittest.mock import mock_open, patch

from skills.report_exporter import ReportExporter, ReportExporterError, export_report


class TestReportExporterInquisition(unittest.TestCase):
    def setUp(self):
        self.random_prefix = f"rnd_{uuid.uuid4().hex[:8]}"

    def _generate_random_string(self, length: int = 12) -> str:
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def _generate_nested_data(self) -> dict:
        return {
            "report_id": f"rep_{uuid.uuid4().hex}",
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "count": random.randint(1, 1000),
            "details": {
                "source_module": f"mod_{self._generate_random_string(6)}",
                "nested_info": {
                    "tag": f"tag_{self._generate_random_string(4)}",
                    "value": random.randint(100, 999),
                },
            },
            "events": [
                f"event_{self._generate_random_string(5)}",
                f"event_{self._generate_random_string(5)}",
            ],
            "complex_list": [
                {"inner_key": f"inner_{self._generate_random_string(6)}"},
                [f"item_{self._generate_random_string(4)}", random.randint(1, 50)],
            ],
        }

    def test_init_validation_success(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        self.assertEqual(exporter.data, data)
        self.assertEqual(exporter.report_id, data["report_id"])

    def test_init_validation_failure_on_non_dict(self):
        invalid_data = random.choice([
            self._generate_random_string(),
            random.randint(1, 100),
            [uuid.uuid4().hex],
            None,
            False,
        ])
        with self.assertRaises(ReportExporterError) as ctx:
            ReportExporter(invalid_data)
        self.assertIn("Audit data must be a dictionary", str(ctx.exception))

    def test_export_json_serialization(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        json_output = exporter.export_json()
        parsed = json.loads(json_output)
        self.assertEqual(parsed, data)
        self.assertEqual(parsed["report_id"], data["report_id"])
        self.assertEqual(parsed["details"]["source_module"], data["details"]["source_module"])

    def test_export_json_failure(self):
        non_serializable_obj = object()
        data = {
            "report_id": f"rep_{uuid.uuid4().hex}",
            "bad_val": non_serializable_obj,
        }
        exporter = ReportExporter(data)
        with self.assertRaises(ReportExporterError) as ctx:
            exporter.export_json()
        self.assertIn("Failed to export to JSON", str(ctx.exception))

    def test_serialize_matches_export_json(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        self.assertEqual(exporter.serialize(), exporter.export_json())

    def test_export_json_to_file_success(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_name = f"{uuid.uuid4().hex}.json"
            target_path = os.path.join(tmp_dir, file_name)
            exporter.export_json_to_file(target_path)
            self.assertTrue(os.path.exists(target_path))
            with open(target_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            self.assertEqual(content, data)

    def test_export_json_to_file_ioerror(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        invalid_path = f"/non_existent_{uuid.uuid4().hex}/file.json"
        with patch("builtins.open", side_effect=OSError("Disk full or permission denied")):
            with self.assertRaises(ReportExporterError) as ctx:
                exporter.export_json_to_file(invalid_path)
            self.assertIn("Failed to write JSON to file", str(ctx.exception))

    def test_export_text_structure(self):
        key_name = f"key_{self._generate_random_string(6)}"
        val_name = f"val_{self._generate_random_string(8)}"
        nested_k = f"nest_{self._generate_random_string(4)}"
        nested_v = f"nval_{self._generate_random_string(5)}"
        list_elem = f"item_{self._generate_random_string(7)}"

        data = {
            key_name: val_name,
            "container": {nested_k: nested_v},
            "array": [list_elem],
        }
        exporter = ReportExporter(data)
        text_out = exporter.export_text()
        self.assertIn(f"{key_name}: {val_name}", text_out)
        self.assertIn(f"container:\n  {nested_k}:\n    {nested_v}", text_out)
        self.assertIn(f"array:\n  - {list_elem}", text_out)

    def test_export_text_to_file_success(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_name = f"{uuid.uuid4().hex}.txt"
            target_path = os.path.join(tmp_dir, file_name)
            exporter.export_text_to_file(target_path)
            self.assertTrue(os.path.exists(target_path))
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(data["report_id"], content)
            self.assertEqual(content, exporter.export_text())

    def test_export_text_to_file_ioerror(self):
        data = self._generate_nested_data()
        exporter = ReportExporter(data)
        with patch("builtins.open", side_effect=PermissionError("Forbidden access")):
            with self.assertRaises(ReportExporterError) as ctx:
                exporter.export_text_to_file(f"/root/{uuid.uuid4().hex}.txt")
            self.assertIn("Failed to write text to file", str(ctx.exception))

    def test_export_custom_text_success(self):
        field_a = f"field_a_{self._generate_random_string(4)}"
        field_b = f"field_b_{self._generate_random_string(4)}"
        val_a = f"alpha_{uuid.uuid4().hex[:6]}"
        val_b = random.randint(1000, 9999)

        data = {field_a: val_a, field_b: val_b}
        template = f"Report [{val_a[:2]}] -> {{{field_a}}} has metric: {{{field_b}}}"
        exporter = ReportExporter(data)
        rendered = exporter.export_custom_text(template)
        expected = f"Report [{val_a[:2]}] -> {val_a} has metric: {val_b}"
        self.assertEqual(rendered, expected)

    def test_export_custom_text_missing_key(self):
        missing_key = f"missing_{self._generate_random_string(6)}"
        template = f"Value: {{{missing_key}}}"
        exporter = ReportExporter({"some_key": self._generate_random_string(5)})
        with self.assertRaises(ReportExporterError) as ctx:
            exporter.export_custom_text(template)
        self.assertIn("Missing key in template", str(ctx.exception))

    def test_export_custom_text_generic_format_error(self):
        exporter = ReportExporter({"num": 123})
        bad_template = "Value: {num:invalid_specifier_xyz}"
        with self.assertRaises(ReportExporterError) as ctx:
            exporter.export_custom_text(bad_template)
        self.assertIn("Failed to format custom text", str(ctx.exception))

    def test_export_report_helper_json(self):
        data = self._generate_nested_data()
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.json")
            export_report(data, target_path, format_type="json")
            self.assertTrue(os.path.exists(target_path))
            with open(target_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, data)

    def test_export_report_helper_text(self):
        data = self._generate_nested_data()
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.txt")
            export_report(data, target_path, format_type="TEXT")
            self.assertTrue(os.path.exists(target_path))
            with open(target_path, "r", encoding="utf-8") as f:
                saved = f.read()
            self.assertIn(data["report_id"], saved)

    def test_export_report_helper_unsupported_format(self):
        data = self._generate_nested_data()
        unsupported = f"fmt_{self._generate_random_string(5)}"
        with self.assertRaises(ReportExporterError) as ctx:
            export_report(data, "/tmp/dummy", format_type=unsupported)
        self.assertIn("Unsupported format type", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()