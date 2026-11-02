import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
from skills.patch_reporter import PatchReporter, PatchReporterError


class TestPatchReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = PatchReporter()
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.analysis_data = {
            "metric": f"metric_{self.rand_suffix}",
            "complexity": random.randint(1, 10)
        }
        self.risk_data = {
            "score": round(random.uniform(0.0, 0.5), 2),
            "risk_level": "LOW"
        }
        self.verification_data = {
            "passed": True,
            "status": "PASSED"
        }

    def test_generate_report_missing_analysis_data(self):
        with self.assertRaises(PatchReporterError):
            self.reporter.generate_report(analysis_data=None, risk_data=self.risk_data)

    def test_generate_report_missing_risk_data(self):
        with self.assertRaises(PatchReporterError):
            self.reporter.generate_report(analysis_data=self.analysis_data, risk_data=None)

    def test_generate_report_invalid_verification_data(self):
        rand_invalid = random.randint(100, 999)
        with self.assertRaises(PatchReporterError):
            self.reporter.generate_report(
                analysis_data=self.analysis_data,
                risk_data=self.risk_data,
                verification_data=rand_invalid
            )

    def test_generate_report_success_derivation(self):
        patch_id = f"patch-{uuid.uuid4().hex[:6]}"
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data,
            patch_id=patch_id
        )
        self.assertEqual(report["patch_id"], patch_id)
        self.assertEqual(report["summary"]["verdict"], "PASSED")
        self.assertTrue(report["summary"]["passed"])

    def test_generate_report_rejection_case(self):
        bad_risk_data = {
            "score": 0.95,
            "risk_level": "CRITICAL"
        }
        bad_verification_data = {
            "passed": False,
            "status": "FAILED"
        }
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=bad_risk_data,
            verification_data=bad_verification_data
        )
        self.assertEqual(report["summary"]["verdict"], "REJECTED")
        self.assertFalse(report["summary"]["passed"])

    def test_generate_report_integration_aliases(self):
        alias_analysis = {"val": uuid.uuid4().hex[:4]}
        alias_risk = {"score": 0.1, "level": "LOW"}
        alias_verification = {"status": "SUCCESS"}
        report = self.reporter.generate_report(
            analysis=alias_analysis,
            risk_assessment=alias_risk,
            verification_results=alias_verification,
            anomalies=[uuid.uuid4().hex]
        )
        self.assertEqual(report["analysis"], alias_analysis)
        self.assertEqual(report["risk_assessment"], alias_risk)
        self.assertEqual(report["verification_results"], alias_verification)
        self.assertIn("anomalies", report)

    def test_export_json_string(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        res = self.reporter.export_json(report)
        self.assertIsInstance(res, str)
        self.assertIn(report["report_id"], res)

    def test_export_json_file(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        filepath = f"/tmp/{uuid.uuid4().hex}.json"
        with patch("builtins.open", mock_open()) as mocked_file:
            path_out = self.reporter.export_json(report, output_path=filepath)
            self.assertEqual(path_out, filepath)
            mocked_file.assert_called_once_with(filepath, "w", encoding="utf-8")

    def test_export_json_os_error(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        filepath = f"/bad/path/{uuid.uuid4().hex}.json"
        with patch("builtins.open", side_effect=OSError("Disk full")):
            with self.assertRaises(PatchReporterError):
                self.reporter.export_json(report, output_path=filepath)

    def test_write_json_stream(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        stream = io.StringIO()
        self.reporter.write_json_stream(report, stream)
        val = stream.getvalue()
        self.assertIn(report["patch_id"], val)

    def test_write_json_stream_error(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        class BadStream:
            def write(self, *args, **kwargs):
                raise Exception("Stream dead")
        
        with self.assertRaises(PatchReporterError):
            self.reporter.write_json_stream(report, BadStream())

    def test_export_markdown_string(self):
        complex_risk = {
            "score": 0.2,
            "risk_level": "LOW",
            "factors": [f"factor_{uuid.uuid4().hex[:4]}"]
        }
        complex_verification = {
            "passed": True,
            "checks": [f"check_{uuid.uuid4().hex[:4]}"]
        }
        metadata = {f"meta_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:4]}
        anomalies = [{"id": uuid.uuid4().hex[:4]}]

        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=complex_risk,
            verification_data=complex_verification,
            metadata=metadata,
            anomalies=anomalies
        )
        md = self.reporter.export_markdown(report)
        self.assertIsInstance(md, str)
        self.assertIn("# Patch Analysis Report:", md)
        self.assertIn("factors", md)
        self.assertIn("checks", md)
        self.assertIn("Metadata", md)
        self.assertIn("Anomalies", md)

    def test_export_markdown_file(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        filepath = f"/tmp/{uuid.uuid4().hex}.md"
        with patch("builtins.open", mock_open()) as mocked_file:
            path_out = self.reporter.export_markdown(report, output_path=filepath)
            self.assertEqual(path_out, filepath)
            mocked_file.assert_called_once_with(filepath, "w", encoding="utf-8")

    def test_export_markdown_os_error(self):
        report = self.reporter.generate_report(
            analysis_data=self.analysis_data,
            risk_data=self.risk_data,
            verification_data=self.verification_data
        )
        filepath = f"/bad/path/{uuid.uuid4().hex}.md"
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with self.assertRaises(PatchReporterError):
                self.reporter.export_markdown(report, output_path=filepath)


if __name__ == "__main__":
    unittest.main()