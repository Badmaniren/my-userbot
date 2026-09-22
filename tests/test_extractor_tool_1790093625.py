import unittest
import os
import uuid
import random
from unittest.mock import patch, mock_open
from skills.extractor_tool_1790093625 import ExtractorTool

class TestExtractorTool(unittest.TestCase):
    def setUp(self):
        self.tool = ExtractorTool()
        self.sample_xml = """
        <root>
            <metadata>
                <entry key="trace_id" value="test_trace_123" />
                <entry key="metric_val" value="42.5" />
                <entry key="label" value="unit_test" />
            </metadata>
        </root>
        """

    def test_initialization(self):
        self.assertEqual(self.tool.extractor_version, "1.0.4-stable")

    def test_extract_metadata_from_markup(self):
        metadata = self.tool.extract_metadata_from_markup(self.sample_xml)
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("trace_id"), "test_trace_123")
        self.assertEqual(metadata.get("metric_val"), "42.5")
        self.assertEqual(metadata.get("label"), "unit_test")
        self.assertIn("processing_timestamp", metadata)
        self.assertEqual(metadata.get("extractor_version"), "1.0.4-stable")
        self.assertIn("operation_id", metadata)

    def test_generate_extraction_report(self):
        prefix = f"prefix_{uuid.uuid4().hex[:6]}"
        expected_filename = f"{prefix}_extraction_log.txt"

        with patch("builtins.open", mock_open()) as mock_file:
            path = self.tool.generate_extraction_report(self.sample_xml, prefix=prefix)
            self.assertTrue(path.endswith(expected_filename))
            mock_file.assert_called_once_with(os.path.abspath(expected_filename), "w", encoding="utf-8")

if __name__ == "__main__":
    unittest.main()
