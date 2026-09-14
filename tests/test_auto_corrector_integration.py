import os
import io
import tempfile
import unittest
from skills.auto_corrector import (
    ErrorAnalyzer,
    AutoCorrector,
    has_critical_errors,
    analyze_errors,
    save_error_report
)


class TestAutoCorrectorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_error_analysis_and_correction(self):
        log_file_path = os.path.join(self.temp_dir.name, "test_error.log")
        log_content = "[CRITICAL] Database connection failed due to timeout."
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(log_content)

        analyzer = ErrorAnalyzer()
        corrector = AutoCorrector()
        report_file_path = os.path.join(self.temp_dir.name, "saved_report.log")

        is_parsed = analyzer.parse_log(log_file_path)
        self.assertTrue(is_parsed)

        with open(log_file_path, "r", encoding="utf-8") as f:
            file_data = f.read()

        critical_found = has_critical_errors(file_data)
        self.assertTrue(critical_found)

        report = analyze_errors(file_data)
        self.assertIsInstance(report, str)
        self.assertIn("CRITICAL", report)

        is_saved = save_error_report(report, report_file_path)
        self.assertTrue(is_saved)
        self.assertTrue(os.path.exists(report_file_path))

        signature = "DB_TIMEOUT_ERROR"
        prevent_result = analyzer.analyze_and_prevent(signature)
        self.assertTrue(prevent_result)

        fix_applied = corrector.apply_fix(signature)
        self.assertTrue(fix_applied)

        stream = io.BytesIO(b"Stream error logs")
        stream_processed = analyzer.process_stream(stream)
        self.assertTrue(stream_processed)


if __name__ == "__main__":
    unittest.main()
