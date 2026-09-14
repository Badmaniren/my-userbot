import os
import unittest
from skills.error_analyzer import ErrorAnalyzer, analyze_errors
from skills.auto_corrector import AutoCorrector

class TestAutoCorrectorIntegration(unittest.TestCase):
    def setUp(self):
        self.log_path = "test_error_log.txt"
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write("ERROR: NullPointerException in module_x at line 42\n")
        
        self.analyzer = ErrorAnalyzer()
        self.corrector = AutoCorrector()

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_end_to_end_error_correction(self):
        parse_result = self.analyzer.parse_log(self.log_path)
        self.assertTrue(parse_result)

        with open(self.log_path, "r", encoding="utf-8") as f:
            logs_content = f.read()

        error_signature = analyze_errors(logs_content)
        self.assertIsInstance(error_signature, str)
        self.assertTrue(len(error_signature) > 0)

        prevention_result = self.analyzer.analyze_and_prevent(error_signature)
        self.assertTrue(prevention_result)

        correction_result = self.corrector.apply_correction(error_signature)
        self.assertTrue(correction_result)

if __name__ == "__main__":
    unittest.main()