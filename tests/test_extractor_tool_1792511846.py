import os
import random
import string
import tempfile
import unittest
import uuid
from unittest.mock import MagicMock, patch

try:
    from skills.extractor_tool_1792511846 import (
        ExtractorTool,
        MetadataExtractionError,
        MetadataExtractor,
        extract_metadata,
    )
except ImportError:
    from extractor_tool_1792511846 import (
        ExtractorTool,
        MetadataExtractionError,
        MetadataExtractor,
        extract_metadata,
    )


def _gen_random_str(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _gen_random_hex():
    return uuid.uuid4().hex


class TestExtractorTool1792511846(unittest.TestCase):

    def setUp(self):
        self.extractor = MetadataExtractor()

    def test_extract_metadata_basic_html(self):
        rand_title = f"Title_{_gen_random_hex()}"
        rand_author_key = f"author_{_gen_random_str(6)}"
        rand_author_val = f"Author_{_gen_random_hex()}"
        rand_desc_val = f"Desc_{_gen_random_hex()}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{rand_title}</title>
            <meta name="{rand_author_key}" content="{rand_author_val}">
            <meta name="description" content="{rand_desc_val}">
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
        </html>
        """
        res = self.extractor.extract(html_content)
        self.assertEqual(res.get("title"), rand_title)
        self.assertEqual(res.get(rand_author_key), rand_author_val)
        self.assertEqual(res.get("description"), rand_desc_val)

    def test_extract_metadata_key_value_pairs(self):
        rand_key = f"KEY_{_gen_random_str(6)}"
        rand_val = f"VAL_{_gen_random_hex()}"
        content = f"METADATA_ID:{_gen_random_hex()} | {rand_key}:{rand_val} | SEVERITY:HIGH"

        res = self.extractor.extract(content)
        self.assertIn("METADATA_ID", res)
        self.assertEqual(res.get(rand_key), rand_val)
        self.assertEqual(res.get("SEVERITY"), "HIGH")

    def test_extract_metadata_xml_tags(self):
        rand_tag = f"tag_{_gen_random_str(6)}"
        rand_val = f"val_{_gen_random_hex()}"
        xml_content = f"<{rand_tag}>{rand_val}</{rand_tag}>"

        res = self.extractor.extract(xml_content)
        self.assertEqual(res.get(rand_tag), rand_val)

    def test_extract_from_file(self):
        rand_key = f"file_key_{_gen_random_str(6)}"
        rand_val = f"file_val_{_gen_random_hex()}"

        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
            tf.write(f"{rand_key}: {rand_val}\n")
            temp_path = tf.name

        try:
            res = self.extractor.extract(temp_path)
            self.assertEqual(res.get(rand_key), rand_val)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_extract_empty_or_whitespace(self):
        self.assertEqual(self.extractor.extract(""), {})
        self.assertEqual(self.extractor.extract("   \n\t  "), {})

    def test_extract_none_raises_error(self):
        with self.assertRaises(MetadataExtractionError):
            self.extractor.extract(None)

    def test_extract_invalid_type_raises_error(self):
        with self.assertRaises(MetadataExtractionError):
            self.extractor.extract(12345)

    def test_top_level_extract_metadata_function(self):
        rand_title = f"Title_{_gen_random_hex()}"
        html = f"<title>{rand_title}</title>"
        res = extract_metadata(html)
        self.assertEqual(res.get("title"), rand_title)

    def test_extractor_tool_class_alias(self):
        tool = ExtractorTool()
        rand_key = f"alias_key_{_gen_random_str(6)}"
        rand_val = f"alias_val_{_gen_random_hex()}"
        res = tool.extract(f"{rand_key} = {rand_val}")
        self.assertEqual(res.get(rand_key), rand_val)


if __name__ == '__main__':
    unittest.main()
