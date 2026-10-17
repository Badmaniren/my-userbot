import io
import json
import os
import random
import string
import sys
import unittest
from unittest.mock import MagicMock, mock_open, patch

try:
    from skills.patch_reporter import PatchReporter, PatchReporterError
except ImportError:
    from patch_reporter import PatchReporter, PatchReporterError


def _rand_str(length: int = 12) -> str:
    letters = string.ascii_letters + string.digits
    return "".join(random.choices(letters, k=length))


def _rand_score() -> float:
    return round(random.uniform(0.0, 1.0), 4)


class TestPatchReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = PatchReporter()

    def _generate_valid_payload(self):
        patch_id = f"patch-{_rand_str(8)}-{_rand_str(4)}"
        component_name = f"module_{_rand_str(6)}"
        metric_loc = random.randint(10, 500)
        risk_score = _rand_score()
        check_name = f"check_{_rand_str(8)}"
        verifier_id = f"verifier_{_rand_str(5)}"
        risk_factor = f"risk_{_rand_str(10)}"

        analysis_data = {
            "patch_id": patch_id,
            "target_component": component_name,
            "metrics": {
                "lines_added": metric_loc,
                "lines_removed": random.randint(0, 100),
                "complexity_delta": random.randint(-5, 15),
            },
            "findings": [
                {
                    "id": f"find-{_rand_str(6)}",
                    "type": random.choice(["CODE_SMELL", "BUG_RISK", "SECURITY_HOTSPOT"]),
                    "description": f"Finding desc {_rand_str(20)}",
                }
            ],
        }

        risk_data = {
            "score": risk_score,
            "risk_level": "HIGH" if risk_score > 0.7 else ("MEDIUM" if risk_score > 0.3 else "LOW"),
            "factors": [risk_factor, f"secondary_{_rand_str(6)}"],
            "requires_manual_approval": risk_score > 0.6,
        }

        verification_data = {
            "verifier_id": verifier_id,
            "passed": random.choice([True, False]),
            "checks": [
                {
                    "name": check_name,
                    "passed": True,
                    "execution_time_ms": random.randint(10, 1500),
                }
            ],
            "trace_id": f"trace-{_rand_str(16)}",
        }

        metadata = {
            "author": f"dev_{_rand_str(6)}@example.com",
            "environment": random.choice(["staging", "production", "ci-runner"]),
            "session_token": f"tok_{_rand_str(24)}",
        }

        return {
            "patch_id": patch_id,
            "component_name": component_name,
            "risk_score": risk_score,
            "risk_factor": risk_factor,
            "check_name": check_name,
            "verifier_id": verifier_id,
            "analysis_data": analysis_data,
            "risk_data": risk_data,
            "verification_data": verification_data,
            "metadata": metadata,
        }

    def test_generate_report_semantic_integrity(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
            metadata=payload["metadata"],
        )

        self.assertIsInstance(report, dict)
        self.assertIn("report_id", report)
        self.assertIn("timestamp", report)
        self.assertIn("summary", report)
        self.assertIn("analysis", report)
        self.assertIn("risks", report)
        self.assertIn("verification", report)
        self.assertIn("metadata", report)

        self.assertEqual(report["analysis"]["patch_id"], payload["patch_id"])
        self.assertEqual(report["analysis"]["target_component"], payload["component_name"])
        self.assertEqual(report["risks"]["score"], payload["risk_score"])
        self.assertIn(payload["risk_factor"], report["risks"]["factors"])
        self.assertEqual(report["verification"]["verifier_id"], payload["verifier_id"])
        self.assertEqual(
            report["verification"]["checks"][0]["name"],
            payload["check_name"],
        )
        self.assertEqual(report["metadata"]["session_token"], payload["metadata"]["session_token"])

    def test_verdict_derivation_pass_case(self):
        payload = self._generate_valid_payload()
        payload["verification_data"]["passed"] = True
        payload["risk_data"]["score"] = 0.15
        payload["risk_data"]["risk_level"] = "LOW"
        payload["risk_data"]["requires_manual_approval"] = False

        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
            metadata=payload["metadata"],
        )

        status = report["summary"].get("status") or report["summary"].get("verdict")
        self.assertIn(status, ["PASSED", "APPROVED", "ACCEPTED"])

    def test_verdict_derivation_rejection_case(self):
        payload = self._generate_valid_payload()
        payload["verification_data"]["passed"] = False
        payload["risk_data"]["score"] = 0.95
        payload["risk_data"]["risk_level"] = "CRITICAL"

        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
            metadata=payload["metadata"],
        )

        status = report["summary"].get("status") or report["summary"].get("verdict")
        self.assertIn(status, ["FAILED", "REJECTED", "BLOCKED"])

    def test_invalid_analysis_input_raises_reporter_error(self):
        payload = self._generate_valid_payload()
        corrupt_inputs = [None, "", 12345, []]

        for bad_analysis in corrupt_inputs:
            with self.assertRaises(PatchReporterError):
                self.reporter.generate_report(
                    analysis_data=bad_analysis,
                    risk_data=payload["risk_data"],
                    verification_data=payload["verification_data"],
                )

    def test_invalid_risk_data_raises_reporter_error(self):
        payload = self._generate_valid_payload()
        corrupt_inputs = [None, "invalid_risk_string", []]

        for bad_risk in corrupt_inputs:
            with self.assertRaises(PatchReporterError):
                self.reporter.generate_report(
                    analysis_data=payload["analysis_data"],
                    risk_data=bad_risk,
                    verification_data=payload["verification_data"],
                )

    def test_export_json_string_content_accuracy(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
            metadata=payload["metadata"],
        )

        json_out = self.reporter.export_json(report)
        self.assertIsInstance(json_out, str)

        parsed = json.loads(json_out)
        self.assertEqual(parsed["analysis"]["patch_id"], payload["patch_id"])
        self.assertEqual(parsed["risks"]["score"], payload["risk_score"])
        self.assertEqual(parsed["metadata"]["session_token"], payload["metadata"]["session_token"])

    def test_export_json_to_file_target(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )
        fake_path = f"/tmp/{_rand_str(10)}/{_rand_str(8)}.json"

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = self.reporter.export_json(report, output_path=fake_path)

        mock_file.assert_called_once_with(fake_path, "w", encoding="utf-8")
        written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
        parsed = json.loads(written_data)
        self.assertEqual(parsed["analysis"]["patch_id"], payload["patch_id"])
        self.assertTrue(result == fake_path or result == written_data)

    def test_export_json_file_io_failure_raises_reporter_error(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )
        fake_path = f"/unwritable/{_rand_str(10)}.json"

        with patch("builtins.open", side_effect=IOError(f"Permission denied: {_rand_str(5)}")):
            with self.assertRaises(PatchReporterError):
                self.reporter.export_json(report, output_path=fake_path)

    def test_export_markdown_structure_and_semantic_tokens(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
            metadata=payload["metadata"],
        )

        md_output = self.reporter.export_markdown(report)
        self.assertIsInstance(md_output, str)

        self.assertIn("# ", md_output)
        self.assertIn("## ", md_output)
        self.assertIn(payload["patch_id"], md_output)
        self.assertIn(payload["component_name"], md_output)
        self.assertIn(payload["verifier_id"], md_output)
        self.assertIn(payload["risk_factor"], md_output)
        self.assertIn(str(payload["risk_score"]), md_output)
        self.assertIn(payload["metadata"]["session_token"], md_output)

    def test_export_markdown_to_file_target(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )
        fake_md_path = f"/tmp/{_rand_str(8)}/{_rand_str(6)}.md"

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = self.reporter.export_markdown(report, output_path=fake_md_path)

        mock_file.assert_called_once_with(fake_md_path, "w", encoding="utf-8")
        written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
        self.assertIn(payload["patch_id"], written_data)
        self.assertTrue(result == fake_md_path or result == written_data)

    def test_export_markdown_io_failure_raises_reporter_error(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )
        fake_path = f"/unwritable/{_rand_str(6)}.md"

        with patch("builtins.open", side_effect=OSError(f"Disk full: {_rand_str(4)}")):
            with self.assertRaises(PatchReporterError):
                self.reporter.export_markdown(report, output_path=fake_path)

    def test_export_to_stream_json(self):
        payload = self._generate_valid_payload()
        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )

        stream = io.StringIO()
        if hasattr(self.reporter, "write_json_stream"):
            self.reporter.write_json_stream(report, stream)
            stream.seek(0)
            parsed = json.loads(stream.read())
            self.assertEqual(parsed["analysis"]["patch_id"], payload["patch_id"])
        else:
            # Fallback if export_json accepts stream
            json_text = self.reporter.export_json(report)
            stream.write(json_text)
            stream.seek(0)
            parsed = json.loads(stream.read())
            self.assertEqual(parsed["analysis"]["patch_id"], payload["patch_id"])

    def test_markdown_special_characters_handled_without_exception(self):
        payload = self._generate_valid_payload()
        special_name = f"component_<script>_`{_rand_str(6)}`_*bold*_{_rand_str(4)}"
        special_factor = f"risk | table | {_rand_str(6)} \n * bullet"
        payload["analysis_data"]["target_component"] = special_name
        payload["risk_data"]["factors"] = [special_factor]

        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )
        md_text = self.reporter.export_markdown(report)
        self.assertIn(special_name, md_text)

    def test_empty_findings_and_checks_produce_clean_report(self):
        payload = self._generate_valid_payload()
        payload["analysis_data"]["findings"] = []
        payload["verification_data"]["checks"] = []
        payload["risk_data"]["factors"] = []

        report = self.reporter.generate_report(
            analysis_data=payload["analysis_data"],
            risk_data=payload["risk_data"],
            verification_data=payload["verification_data"],
        )

        self.assertEqual(report["analysis"]["findings"], [])
        self.assertEqual(report["verification"]["checks"], [])
        self.assertEqual(report["risks"]["factors"], [])

        md = self.reporter.export_markdown(report)
        self.assertIsInstance(md, str)
        self.assertIn(payload["patch_id"], md)


if __name__ == "__main__":
    unittest.main()