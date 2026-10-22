import unittest
import tempfile
import shutil
import os
import uuid
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from skills.extractor_tool_1792686109 import ExtractorTool, ExtractorToolError


class TestExtractorTool1792686109Integration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.extractor = ExtractorTool()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_extract_from_file_real_filesystem(self):
        file_path = os.path.join(self.test_dir, f"metadata_{uuid.uuid4().hex[:6]}.html")
        author_name = f"author_{uuid.uuid4().hex[:8]}"
        project_title = f"project_{uuid.uuid4().hex[:8]}"

        markup_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta name="author" content="{author_name}">
    <meta property="title" content="{project_title}">
</head>
<body>
    <h1>Welcome</h1>
</body>
</html>
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markup_content)

        extracted = self.extractor.extract_from_file(file_path)

        self.assertIsInstance(extracted, dict)
        self.assertEqual(extracted.get("author"), author_name)
        self.assertEqual(extracted.get("title"), project_title)

    def test_extract_tags_and_parse_attributes_integration(self):
        file_path = os.path.join(self.test_dir, f"data_{uuid.uuid4().hex[:6]}.xml")
        item_id_1 = f"id_{uuid.uuid4().hex[:4]}"
        item_id_2 = f"id_{uuid.uuid4().hex[:4]}"
        val_1 = f"val_{uuid.uuid4().hex[:6]}"
        val_2 = f"val_{uuid.uuid4().hex[:6]}"

        xml_content = f"""<root>
    <item id="{item_id_1}" type="primary">{val_1}</item>
    <item id="{item_id_2}" type="secondary">{val_2}</item>
</root>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tags = self.extractor.extract_tags(content, "item")

        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0]["attributes"].get("id"), item_id_1)
        self.assertEqual(tags[0]["attributes"].get("type"), "primary")
        self.assertEqual(tags[0]["content"], val_1)
        self.assertEqual(tags[1]["attributes"].get("id"), item_id_2)
        self.assertEqual(tags[1]["attributes"].get("type"), "secondary")
        self.assertEqual(tags[1]["content"], val_2)


if __name__ == "__main__":
    unittest.main()
