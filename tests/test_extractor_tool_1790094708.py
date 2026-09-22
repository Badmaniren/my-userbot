import unittest
import os
from skills.extractor_tool_1790094708 import ExtractorTool

class TestExtractorToolUnit(unittest.TestCase):
    def setUp(self):
        self.tool = ExtractorTool()
        self.sample_markup = """
        <root>
            <metadata>
                <entry key="trace_id" value="test-trace-123" />
                <entry key="metric_val" value="42.5" />
                <entry key="label" value="unit-test-label" />
            </metadata>
        </root>
        """

    def test_extract_metadata_from_markup_structure(self):
        metadata = self.tool.extract_metadata_from_markup(self.sample_markup)
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("trace_id"), "test-trace-123")
        self.assertEqual(metadata.get("metric_val"), "42.5")
        self.assertEqual(metadata.get("label"), "unit-test-label")
        self.assertIn("processing_timestamp", metadata)
        self.assertIn("extractor_version", metadata)
        self.assertIn("operation_id", metadata)

    def test_generate_extraction_report_file_creation(self):
        prefix = "unit_test_run"
        file_path = self.tool.generate_extraction_report(self.sample_markup, prefix=prefix)
        try:
            self.assertTrue(os.path.isabs(file_path))
            self.assertTrue(os.path.exists(file_path))
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("--- Extraction Report ---", content)
                self.assertIn("test-trace-123", content)
                self.assertIn("unit-test-label", content)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    unittest.main()
