import unittest
import uuid
import random
from skills.extractor_tool_1790102839 import ExtractorTool, extract_metadata


class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = ExtractorTool()

    def test_integration_extraction_pipeline(self) -> None:
        random_id = str(uuid.uuid4())
        random_author_id = f"author_{random.randint(1000, 9999)}"
        random_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}"

        markup = f"""---
title: "Document {random_id}"
version: {random_version}
---
<!DOCTYPE html>
<html>
<head>
    <meta name="author" content="{random_author_id}">
    <meta name="doc-id" content="{random_id}">
    <script type="application/json">
    {{
        "json_key_{random_id}": "json_value_{random_id}",
        "numeric_metric": {random.randint(100, 999)}
    }}
    </script>
</head>
<body>
    <h1>Test Markup</h1>
</body>
</html>
"""

        result = self.extractor.extract(markup)

        self.assertEqual(result.get("title"), f"Document {random_id}")
        self.assertEqual(result.get("version"), random_version)
        self.assertEqual(result.get("author"), random_author_id)
        self.assertEqual(result.get("doc-id"), random_id)
        self.assertEqual(result.get(f"json_key_{random_id}"), f"json_value_{random_id}")
        self.assertIn("numeric_metric", result)

        helper_result = extract_metadata(markup)
        self.assertEqual(helper_result.get("doc-id"), random_id)
        self.assertEqual(helper_result.get(f"json_key_{random_id}"), f"json_value_{random_id}")


if __name__ == "__main__":
    unittest.main()