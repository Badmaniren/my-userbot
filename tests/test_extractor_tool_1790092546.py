import unittest
from unittest.mock import patch, mock_open
import uuid
import random
from skills.extractor_tool_1790092546 import ExtractorTool

class TestExtractorToolUnit(unittest.TestCase):
    def setUp(self):
        self.tool = ExtractorTool()
        self.random_id = str(uuid.uuid4())
        self.random_metric = random.uniform(0.001, 999.999)
        self.random_tag = f"tag_{random.randint(1000, 9999)}"
        self.markup_data = f"""
        <root>
            <metadata>
                <entry key="trace_id" value="{self.random_id}" />
                <entry key="metric_val" value="{self.random_metric}" />
                <entry key="label" value="{self.random_tag}" />
            </metadata>
        </root>
        """

    def test_init(self):
        self.assertEqual(self.tool.extractor_version, "1.0.4-stable")

    def test_extract_metadata_from_markup(self):
        res = self.tool.extract_metadata_from_markup(self.markup_data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("trace_id"), self.random_id)
        self.assertEqual(float(res.get("metric_val")), self.random_metric)
        self.assertEqual(res.get("label"), self.random_tag)
        self.assertIn("processing_timestamp", res)
        self.assertIn("extractor_version", res)
        self.assertIn("operation_id", res)

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_extraction_report(self, mock_file):
        prefix = f"prefix_{random.randint(100, 999)}"
        file_path = self.tool.generate_extraction_report(self.markup_data, prefix=prefix)
        self.assertTrue(file_path.endswith(f"{prefix}_extraction_log.txt"))
        mock_file.assert_called_once()

if __name__ == "__main__":
    unittest.main()
