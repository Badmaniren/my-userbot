import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import string
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from skills.extractor_tool_1792686109 import (
    MetadataExtractor,
    ExtractorTool,
    MetadataExtractionError,
    ExtractorToolError,
    extract_metadata
)


class TestExtractorTool1792686109(unittest.TestCase):

    def setUp(self):
        self.rand_key = f"author_{uuid.uuid4().hex[:6]}"
        self.rand_val = f"user_{uuid.uuid4().hex[:8]}"
        self.extractor = ExtractorTool()

    def test_exceptions_hierarchy(self):
        err_msg = f"Error {uuid.uuid4().hex}"
        err = ExtractorToolError(err_msg)
        self.assertIsInstance(err, MetadataExtractionError)
        self.assertEqual(str(err), err_msg)

    def test_extract_metadata_key_value(self):
        key = f"title_{uuid.uuid4().hex[:6]}"
        val = f"Document_{uuid.uuid4().hex[:8]}"
        markup = f"{key}: {val}"

        res = self.extractor.extract(markup)
        self.assertIn(key.lower(), res)
        self.assertEqual(res[key.lower()], val)

    def test_extract_metadata_html_meta(self):
        key = f"description_{uuid.uuid4().hex[:6]}"
        val = f"Sample page {uuid.uuid4().hex[:8]}"
        markup = f'<html><head><meta name="{key}" content="{val}"></head></html>'

        res = self.extractor.extract(markup)
        self.assertIn(key, res)
        self.assertEqual(res[key], val)

    def test_parse_attributes(self):
        attr_name = f"data_id_{uuid.uuid4().hex[:4]}"
        attr_val = f"val_{uuid.uuid4().hex[:6]}"
        tag_str = f'<div class="container" {attr_name}="{attr_val}">'

        attrs = self.extractor.parse_attributes(tag_str)
        self.assertIn("class", attrs)
        self.assertEqual(attrs["class"], "container")
        self.assertIn(attr_name, attrs)
        self.assertEqual(attrs[attr_name], attr_val)

    def test_extract_tags(self):
        tag_name = "item"
        id_val = uuid.uuid4().hex[:6]
        content_val = f"Content_{uuid.uuid4().hex[:8]}"
        markup = f'<{tag_name} id="{id_val}">{content_val}</{tag_name}>'

        tags = self.extractor.extract_tags(markup, tag_name)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["tag"], tag_name)
        self.assertEqual(tags[0]["attributes"].get("id"), id_val)
        self.assertEqual(tags[0]["content"], content_val)

    def test_extract_from_file_mock(self):
        filepath = f"/tmp/test_{uuid.uuid4().hex}.txt"
        key = f"version_{uuid.uuid4().hex[:4]}"
        val = f"1.{random.randint(0, 99)}.0"
        file_content = f"{key}: {val}"

        with patch("builtins.open", mock_open(read_data=file_content)):
            res = self.extractor.extract_from_file(filepath)
            self.assertIn(key.lower(), res)
            self.assertEqual(res[key.lower()], val)

    def test_extract_from_file_raises_error(self):
        filepath = f"/non_existent_{uuid.uuid4().hex}.txt"
        with self.assertRaises(ExtractorToolError):
            self.extractor.extract_from_file(filepath)

    def test_standalone_extract_metadata_function(self):
        key = f"status_{uuid.uuid4().hex[:4]}"
        val = "active"
        markup = f"{key}: {val}"

        res = extract_metadata(markup)
        self.assertEqual(res.get(key.lower()), val)


if __name__ == "__main__":
    unittest.main()
