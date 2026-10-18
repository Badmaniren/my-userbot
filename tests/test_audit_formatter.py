import json
import random
import string
import unittest
import uuid
from unittest.mock import mock_open, patch

from skills.audit_formatter import AuditFormatter, AuditFormatterError


def _rand_str(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _generate_random_anomaly():
    return {
        "id": f"anom-{uuid.uuid4().hex}",
        "source": f"module_{_rand_str(8)}",
        "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL", f"CUSTOM_{_rand_str(4).upper()}"]),
        "timestamp": f"2026-03-{random.randint(10, 28):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}Z",
        "details": f"Anomaly detected in {_rand_str(16)}: value={random.uniform(10.0, 999.9):.2f}",
        "telemetry_snapshot": {
            f"metric_{_rand_str(6)}": round(random.uniform(0.1, 100.0), 3),
            f"flag_{_rand_str(4)}": random.choice([True, False]),
            f"node_{_rand_str(5)}": _rand_str(10),
        },
    }


def _generate_random_report(anomalies_count=None):
    if anomalies_count is None:
        anomalies_count = random.randint(2, 6)
    anomalies = [_generate_random_anomaly() for _ in range(anomalies_count)]
    severities = {}
    for a in anomalies:
        sev = a["severity"]
        severities[sev] = severities.get(sev, 0) + 1

    return {
        "report_id": f"rep-{uuid.uuid4().hex}",
        "environment": f"env-{_rand_str(6)}",
        "repo_path": f"/var/repo/{_rand_str(8)}/{_rand_str(5)}",
        "total_anomalies": len(anomalies),
        "severity_distribution": severities,
        "anomalies": anomalies,
        "generated_by": f"agent_{_rand_str(7)}",
    }


class TestAuditFormatterExceptions(unittest.TestCase):

    def test_exception_inheritance(self):
        err_msg = f"err_{_rand_str(16)}"
        exc = AuditFormatterError(err_msg)
        self.assertIsInstance(exc, Exception)
        self.assertEqual(str(exc), err_msg)


class TestAuditFormatterJSON(unittest.TestCase):

    def setUp(self):
        self.formatter = AuditFormatter()

    def test_format_json_valid_report(self):
        report = _generate_random_report(anomalies_count=random.randint(2, 5))
        json_output = self.formatter.format_json(report)

        self.assertIsInstance(json_output, str)
        parsed = json.loads(json_output)

        self.assertEqual(parsed["report_id"], report["report_id"])
        self.assertEqual(parsed["environment"], report["environment"])
        self.assertEqual(parsed["repo_path"], report["repo_path"])
        self.assertEqual(len(parsed["anomalies"]), len(report["anomalies"]))

        for orig_anom, parsed_anom in zip(report["anomalies"], parsed["anomalies"]):
            self.assertEqual(orig_anom["id"], parsed_anom["id"])
            self.assertEqual(orig_anom["source"], parsed_anom["source"])
            self.assertEqual(orig_anom["severity"], parsed_anom["severity"])
            self.assertEqual(orig_anom["details"], parsed_anom["details"])
            self.assertEqual(orig_anom["telemetry_snapshot"], parsed_anom["telemetry_snapshot"])

    def test_format_json_with_indentation(self):
        report = _generate_random_report(anomalies_count=1)
        indent_val = random.randint(3, 6)
        formatted_str = self.formatter.format_json(report, indent=indent_val)
        expected_spaces = " " * indent_val
        self.assertIn(f"\n{expected_spaces}", formatted_str)

    def test_format_json_invalid_input_type(self):
        invalid_inputs = [
            random.randint(100, 999),
            f"string_not_dict_{_rand_str(10)}",
            None,
            [_rand_str(5)],
        ]
        for bad_input in invalid_inputs:
            with self.assertRaises(AuditFormatterError):
                self.formatter.format_json(bad_input)

    def test_format_json_unserializable_data(self):
        class NonSerializableObj:
            def __repr__(self):
                return _rand_str(8)

        unserializable_report = {
            "report_id": f"rep-{uuid.uuid4().hex}",
            "bad_field": NonSerializableObj(),
        }
        with self.assertRaises(AuditFormatterError):
            self.formatter.format_json(unserializable_report)


class TestAuditFormatterMarkdown(unittest.TestCase):

    def setUp(self):
        self.formatter = AuditFormatter()

    def test_format_markdown_contains_core_metadata(self):
        report = _generate_random_report(anomalies_count=random.randint(1, 3))
        md = self.formatter.format_markdown(report)

        self.assertIsInstance(md, str)
        self.assertIn(report["report_id"], md)
        self.assertIn(report["environment"], md)
        self.assertIn(str(report["total_anomalies"]), md)

        for anom in report["anomalies"]:
            self.assertIn(anom["id"], md)
            self.assertIn(anom["source"], md)
            self.assertIn(anom["severity"], md)
            self.assertIn(anom["details"], md)

    def test_format_markdown_severity_breakdown(self):
        report = _generate_random_report(anomalies_count=random.randint(3, 6))
        md = self.formatter.format_markdown(report)

        for sev, count in report["severity_distribution"].items():
            self.assertIn(sev, md)
            self.assertIn(str(count), md)

    def test_format_markdown_telemetry_snapshot(self):
        report = _generate_random_report(anomalies_count=1)
        single_anom = report["anomalies"][0]
        md = self.formatter.format_markdown(report)

        for metric_key, metric_val in single_anom["telemetry_snapshot"].items():
            self.assertIn(metric_key, md)
            self.assertIn(str(metric_val), md)

    def test_format_markdown_empty_anomalies(self):
        empty_report = {
            "report_id": f"rep-{uuid.uuid4().hex}",
            "environment": f"env-{_rand_str(5)}",
            "repo_path": f"/path/{_rand_str(6)}",
            "total_anomalies": 0,
            "severity_distribution": {},
            "anomalies": [],
        }
        md = self.formatter.format_markdown(empty_report)
        self.assertIsInstance(md, str)
        self.assertIn(empty_report["report_id"], md)
        self.assertIn("0", md)

    def test_format_markdown_invalid_input(self):
        with self.assertRaises(AuditFormatterError):
            self.formatter.format_markdown(None)

        with self.assertRaises(AuditFormatterError):
            self.formatter.format_markdown(f"not_a_dict_{_rand_str(8)}")


class TestAuditFormatterSummary(unittest.TestCase):

    def setUp(self):
        self.formatter = AuditFormatter()

    def test_format_summary_contains_essential_counts_and_identifiers(self):
        report = _generate_random_report(anomalies_count=random.randint(2, 4))
        summary = self.formatter.format_summary(report)

        self.assertIsInstance(summary, str)
        self.assertIn(report["report_id"], summary)
        self.assertIn(str(report["total_anomalies"]), summary)

        for sev, count in report["severity_distribution"].items():
            self.assertIn(sev, summary)
            self.assertIn(str(count), summary)

        # Plain text summary should include anomaly sources or details
        for anom in report["anomalies"]:
            self.assertIn(anom["source"], summary)

    def test_format_summary_invalid_input(self):
        with self.assertRaises(AuditFormatterError):
            self.formatter.format_summary([])

        with self.assertRaises(AuditFormatterError):
            self.formatter.format_summary(random.randint(1, 1000))


class TestAuditFormatterUnifiedInterface(unittest.TestCase):

    def setUp(self):
        self.formatter = AuditFormatter()

    def test_format_dispatch_json(self):
        report = _generate_random_report(anomalies_count=2)
        target_fmt = random.choice(["json", "JSON", "Json"])
        result = self.formatter.format(report, output_format=target_fmt)
        parsed = json.loads(result)
        self.assertEqual(parsed["report_id"], report["report_id"])

    def test_format_dispatch_markdown(self):
        report = _generate_random_report(anomalies_count=2)
        target_fmt = random.choice(["markdown", "MARKDOWN", "md", "MD"])
        result = self.formatter.format(report, output_format=target_fmt)
        self.assertIn(report["report_id"], result)
        self.assertIn(report["environment"], result)

    def test_format_dispatch_summary(self):
        report = _generate_random_report(anomalies_count=2)
        target_fmt = random.choice(["summary", "SUMMARY", "text", "TEXT", "txt", "TXT"])
        result = self.formatter.format(report, output_format=target_fmt)
        self.assertIn(report["report_id"], result)
        self.assertIn(str(report["total_anomalies"]), result)

    def test_format_dispatch_unsupported_format(self):
        report = _generate_random_report(anomalies_count=1)
        bad_format = f"unsupported_{_rand_str(8)}"
        with self.assertRaises(AuditFormatterError) as ctx:
            self.formatter.format(report, output_format=bad_format)
        self.assertIn(bad_format, str(ctx.exception))

    def test_format_missing_format_argument_defaults_to_json(self):
        report = _generate_random_report(anomalies_count=1)
        result = self.formatter.format(report)
        parsed = json.loads(result)
        self.assertEqual(parsed["report_id"], report["report_id"])


class TestAuditFormatterFileOperations(unittest.TestCase):

    def setUp(self):
        self.formatter = AuditFormatter()

    def test_export_to_file_json(self):
        report = _generate_random_report(anomalies_count=2)
        rand_path = f"/tmp/{_rand_str(10)}/report_{uuid.uuid4().hex}.json"

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            self.formatter.export_to_file(report, file_path=rand_path, output_format="json")

        mock_file.assert_called_once_with(rand_path, "w", encoding="utf-8")
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        parsed = json.loads(written_content)
        self.assertEqual(parsed["report_id"], report["report_id"])

    def test_export_to_file_markdown(self):
        report = _generate_random_report(anomalies_count=2)
        rand_path = f"/var/log/{_rand_str(8)}/audit_{uuid.uuid4().hex}.md"

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            self.formatter.export_to_file(report, file_path=rand_path, output_format="markdown")

        mock_file.assert_called_once_with(rand_path, "w", encoding="utf-8")
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        self.assertIn(report["report_id"], written_content)
        self.assertIn(report["environment"], written_content)

    def test_export_to_file_io_error_triggers_audit_formatter_error(self):
        report = _generate_random_report(anomalies_count=1)
        rand_path = f"/restricted/{_rand_str(12)}.json"
        io_error_msg = f"Permission denied: {_rand_str(10)}"

        with patch("builtins.open", side_effect=IOError(io_error_msg)):
            with self.assertRaises(AuditFormatterError) as ctx:
                self.formatter.export_to_file(report, file_path=rand_path, output_format="json")
            self.assertIn(io_error_msg, str(ctx.exception))


class TestAuditFormatterRobustness(unittest.TestCase):

    def setUp(self):
        self.formatter = AuditFormatter()

    def test_missing_optional_keys_does_not_crash_markdown(self):
        sparse_report = {
            "report_id": f"sparse-{uuid.uuid4().hex}",
            "anomalies": [
                {
                    "source": f"sparse_src_{_rand_str(6)}",
                    "details": f"sparse_detail_{_rand_str(8)}",
                }
            ],
        }
        md = self.formatter.format_markdown(sparse_report)
        self.assertIn(sparse_report["report_id"], md)
        self.assertIn(sparse_report["anomalies"][0]["source"], md)
        self.assertIn(sparse_report["anomalies"][0]["details"], md)

    def test_missing_optional_keys_does_not_crash_summary(self):
        sparse_report = {
            "report_id": f"sparse-{uuid.uuid4().hex}",
            "anomalies": [
                {
                    "source": f"agent_{_rand_str(6)}",
                }
            ],
        }
        summary = self.formatter.format_summary(sparse_report)
        self.assertIn(sparse_report["report_id"], summary)
        self.assertIn(sparse_report["anomalies"][0]["source"], summary)

    def test_large_random_payload(self):
        report = _generate_random_report(anomalies_count=random.randint(30, 60))
        json_out = self.formatter.format(report, "json")
        md_out = self.formatter.format(report, "markdown")
        sum_out = self.formatter.format(report, "summary")

        self.assertTrue(len(json_out) > 500)
        self.assertTrue(len(md_out) > 500)
        self.assertTrue(len(sum_out) > 200)

        # Check random anomaly sampled from large report exists in all outputs
        sample_anom = random.choice(report["anomalies"])
        self.assertIn(sample_anom["source"], json_out)
        self.assertIn(sample_anom["source"], md_out)
        self.assertIn(sample_anom["source"], sum_out)


if __name__ == "__main__":
    unittest.main()