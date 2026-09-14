import unittest
from skills.error_log_parser import ErrorLogParser


class TestErrorLogParserIntegration(unittest.TestCase):

    def test_error_log_parser_integration(self):
        parser = ErrorLogParser()
        raw_log = "CRITICAL: Database connection timeout in module auth_service during round 3."

        parsed_result = parser.parse(raw_log)
        self.assertIsInstance(parsed_result, str)
        self.assertGreater(len(parsed_result), 0)

        is_categorized = parser.categorize(parsed_result)
        self.assertIsInstance(is_categorized, bool)
        self.assertTrue(is_categorized)