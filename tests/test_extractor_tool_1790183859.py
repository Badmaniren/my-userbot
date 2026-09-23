import os
import tempfile
import unittest
import uuid
from skills.extractor_tool_1790183859 import (
    ExtractorTool,
    extract_metadata,
    extract_metadata_from_file,
)


class TestExtractorTool1790183859Unit(unittest.TestCase):

    def setUp(self) -> None:
        self.tool = ExtractorTool()

    def test_extract_metadata_from_markup_empty_or_invalid(self):
        res1 = self.tool.extract_metadata_from_markup("")
        self.assertEqual(res1, {"metadata": {}})

        res2 = self.tool.extract_metadata_from_markup(None)
        self.assertEqual(res2, {"metadata": {}})

    def test_extract_metadata_html_and_extract_alias(self):
        markup = '<meta name="description" content="Test Content"><meta name="version" content="100">'
        res = self.tool.extract_metadata_from_markup(markup)
        self.assertEqual(res["metadata"]["description"], "Test Content")
        self.assertEqual(res["metadata"]["version"], 100)

        res_extract = self.tool.extract(markup)
        self.assertEqual(res_extract["description"], "Test Content")

    def test_extract_structured_comment_and_script(self):
        markup = """
        <!-- metadata: {"key_c": "val_c", "num_c": 42} -->
        <script type="application/json">
        {"key_s": "val_s", "bool_s": true}
        </script>
        """
        res = extract_metadata(markup)
        meta = res["metadata"]
        self.assertEqual(meta["key_c"], "val_c")
        self.assertEqual(meta["num_c"], 42)
        self.assertEqual(meta["key_s"], "val_s")
        self.assertTrue(meta["bool_s"])

    def test_extract_xml_entry_tags(self):
        markup = '<entry key="param1" value="val1"/><entry key="param2" value="123"/>'
        res = self.tool.extract_metadata_from_markup(markup)
        meta = res["metadata"]
        self.assertEqual(meta["param1"], "val1")
        self.assertEqual(meta["param2"], "123")

    def test_extract_metadata_from_file_nonexistent(self):
        res = extract_metadata_from_file("non_existent_file_xyz_123.md")
        self.assertEqual(res["metadata"], {})
        self.assertIn("error", res)

    def test_extract_metadata_from_file_success(self):
        test_uuid = str(uuid.uuid4())
        content = f"""---
title: Sample Frontmatter
uuid: {test_uuid}
enabled: true
number: 123
---
# Body
Sample body.
"""
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            filepath = f.name
            f.write(content)

        try:
            res = extract_metadata_from_file(filepath)
            self.assertEqual(res["source_file"], filepath)
            meta = res["metadata"]
            self.assertEqual(meta["title"], "Sample Frontmatter")
            self.assertEqual(meta["uuid"], test_uuid)
            self.assertTrue(meta["enabled"])
            self.assertEqual(meta["number"], 123)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == "__main__":
    unittest.main()
