import os
import tempfile
import unittest
from skills.error_analyzer import analyze_error_log, is_recursive_failure


class TestErrorAnalyzerIntegration(unittest.TestCase):

    def test_error_analyzer_integration(self):
        log_content = (
            "CRITICAL: Test failed due to NullPointerException in auth_module.\n"
            "Caused by: Token is expired."
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as tmp:
            tmp.write(log_content)
            tmp_path = tmp.name

        try:
            analysis_result = analyze_error_log(tmp_path)
            self.assertIsInstance(analysis_result, str)
            self.assertGreater(len(analysis_result), 0)

            is_recursive = is_recursive_failure(analysis_result)
            self.assertIsInstance(is_recursive, bool)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
