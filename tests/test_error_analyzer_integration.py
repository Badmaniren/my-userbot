import os
import io
import tempfile
import unittest
from skills.error_analyzer import (
    ErrorAnalyzer,
    has_critical_errors,
    analyze_errors,
    save_error_report
)


class TestErrorAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = ErrorAnalyzer()
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_full_error_processing_pipeline(self):
        log_content = b"CRITICAL: NullPointerException at module startup"
        with open(self.temp_file.name, "wb") as f:
            f.write(log_content)

        is_parsed = self.analyzer.parse_log(self.temp_file.name)
        self.assertTrue(is_parsed)

        with open(self.temp_file.name, "r", encoding="utf-8") as f:
            logs_str = f.read()

        has_critical = has_critical_errors(logs_str)
        self.assertTrue(has_critical)

        should_prevent = self.analyzer.analyze_and_prevent("NullPointerException")
        self.assertTrue(should_prevent)

        report = analyze_errors(logs_str)
        self.assertIsInstance(report, str)
        self.assertTrue(len(report) > 0)

        saved = save_error_report(report)
        self.assertTrue(saved)

    def test_stream_processing_pipeline(self):
        valid_stream = io.BytesIO(b"Normal log execution flow without errors")
        result = self.analyzer.process_stream(valid_stream)
        self.assertTrue(result)

        corrupted_stream = io.BytesIO(b"Stream contains corrupted data")
        with self.assertRaises(ValueError):
            self.analyzer.process_stream(corrupted_stream)

        crash_stream = io.BytesIO(b"Stream contains bad data causing crash")
        crash_result = self.analyzer.process_stream(crash_stream)
        self.assertFalse(crash_result)


if __name__ == "__main__":
    unittest.main()