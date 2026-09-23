import unittest
import uuid
import random
import os
from skills.extractor_tool_1790177682 import ExtractorTool, extract_metadata


class TestExtractorTool1790177682Integration(unittest.TestCase):

    def setUp(self) -> None:
        self.tool = ExtractorTool()
        self.random_id = str(uuid.uuid4())
        self.random_metric = random.uniform(0.001, 999.999)
        self.random_tag = f"tag_{random.randint(1000, 9999)}"

        self.markup_data = f"""---
author: "Author_{self.random_tag}"
---
<root>
    <metadata>
        <entry key="trace_id" value="{self.random_id}" />
        <entry key="metric_val" value="{self.random_metric}" />
        <entry key="label" value="{self.random_tag}" />
    </metadata>
</root>
"""

    def test_extraction_integration_flow(self) -> None:
        result = self.tool.extract_metadata_from_markup(self.markup_data)

        self.assertIsNotNone(result, "Результат извлечения не должен быть пустым")
        self.assertEqual(result.get("trace_id"), self.random_id)
        self.assertEqual(float(result.get("metric_val")), self.random_metric)
        self.assertEqual(result.get("label"), self.random_tag)
        self.assertEqual(result.get("author"), f"Author_{self.random_tag}")

        self.assertIn("processing_timestamp", result)
        self.assertIn("extractor_version", result)
        self.assertIn("operation_id", result)

        helper_res = extract_metadata(self.markup_data)
        self.assertEqual(helper_res.get("trace_id"), self.random_id)

    def test_operation_id_uniqueness(self) -> None:
        res1 = self.tool.extract_metadata_from_markup(self.markup_data)
        res2 = self.tool.extract_metadata_from_markup(self.markup_data)

        op1 = res1.get("operation_id")
        op2 = res2.get("operation_id")

        self.assertIsNotNone(op1)
        self.assertIsNotNone(op2)
        self.assertNotEqual(op1, op2, "ID операций должны быть уникальными для каждого вызова")

    def test_file_artifact_creation(self) -> None:
        test_prefix = f"test_run_{random.randint(1, 100000)}_{uuid.uuid4().hex[:6]}"
        artifact_path = self.tool.generate_extraction_report(self.markup_data, prefix=test_prefix)

        try:
            self.assertTrue(os.path.exists(artifact_path), f"Файл отчета {artifact_path} должен быть создан")
            with open(artifact_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(self.random_id, content)
                self.assertIn("--- Extraction Report ---", content)
        finally:
            if os.path.exists(artifact_path):
                os.remove(artifact_path)


if __name__ == "__main__":
    unittest.main()
