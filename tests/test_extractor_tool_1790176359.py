import unittest
import uuid
import random
import os
from skills.extractor_tool_1790176359 import ExtractorTool, extract_metadata


class TestExtractorTool1790176359(unittest.TestCase):
    def setUp(self):
        self.tool = ExtractorTool()
        self.random_id = str(uuid.uuid4())
        self.random_metric = random.uniform(0.001, 999.999)
        self.random_tag = f"tag_{random.randint(1000, 9999)}"

        self.xml_markup = f"""
        <root>
            <metadata>
                <entry key="trace_id" value="{self.random_id}" />
                <entry key="metric_val" value="{self.random_metric}" />
                <entry key="label" value="{self.random_tag}" />
            </metadata>
        </root>
        """

        self.html_json_markup = f"""
        <html>
            <head>
                <meta name="author" content="TestAuthor" />
                <script type="application/json">
                {{
                    "trace_id": "{self.random_id}",
                    "metric_val": {self.random_metric},
                    "label": "{self.random_tag}"
                }}
                </script>
            </head>
        </html>
        """

    def test_extract_xml_metadata(self):
        res = self.tool.extract_metadata_from_markup(self.xml_markup)
        self.assertEqual(res.get("trace_id"), self.random_id)
        self.assertEqual(float(res.get("metric_val")), self.random_metric)
        self.assertEqual(res.get("label"), self.random_tag)
        self.assertIn("processing_timestamp", res)
        self.assertIn("operation_id", res)

    def test_extract_html_json_metadata(self):
        res = self.tool.extract(self.html_json_markup)
        self.assertEqual(res.get("author"), "TestAuthor")
        self.assertEqual(res.get("trace_id"), self.random_id)
        self.assertEqual(res.get("metric_val"), self.random_metric)

    def test_extract_metadata_helper_function(self):
        res = extract_metadata(self.xml_markup)
        self.assertEqual(res.get("trace_id"), self.random_id)

    def test_invalid_and_empty_inputs(self):
        res_empty = self.tool.extract_metadata_from_markup("")
        self.assertIn("operation_id", res_empty)

        res_none = self.tool.extract_metadata_from_markup(None)
        self.assertIn("operation_id", res_none)

    def test_generate_extraction_report(self):
        prefix = f"report_{random.randint(1000, 9999)}"
        report_path = self.tool.generate_extraction_report(self.xml_markup, prefix)
        try:
            self.assertTrue(os.path.exists(report_path))
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("--- Extraction Report ---", content)
            self.assertIn(self.random_id, content)
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)


if __name__ == "__main__":
    unittest.main()
