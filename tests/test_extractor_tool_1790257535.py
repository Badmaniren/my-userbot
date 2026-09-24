import json
import os
import random
import unittest
import uuid
from skills.extractor_tool_1790257535 import ExtractorTool, extract, extract_metadata


class TestExtractorTool1790257535(unittest.TestCase):

    def setUp(self):
        self.tool = ExtractorTool()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.meta_name = f"meta_{self.random_prefix}"
        self.meta_content = f"content_{uuid.uuid4().hex[:8]}"
        self.json_key = f"key_{self.random_prefix}"
        self.json_val = f"val_{uuid.uuid4().hex[:8]}"
        self.fm_key = f"fm_{self.random_prefix}"
        self.fm_val = f"val_fm_{uuid.uuid4().hex[:8]}"
        self.report_path = None

    def tearDown(self):
        if self.report_path and os.path.exists(self.report_path):
            try:
                os.remove(self.report_path)
            except OSError:
                pass

    def test_extract_invalid_input(self):
        invalid_inputs = [None, 12345, ["some", "markup"], {"markup": "data"}, 123.45, True]
        for item in invalid_inputs:
            with self.subTest(item=item):
                res = self.tool.extract(item)
                self.assertEqual(res, {})

    def test_extract_meta_tags_and_title(self):
        title = f"Page_{self.random_prefix}"
        markup = f'<html><head><title>{title}</title><meta name="{self.meta_name}" content="{self.meta_content}"></head></html>'
        res = self.tool.extract(markup)
        self.assertEqual(res.get("title"), title)
        self.assertEqual(res.get(self.meta_name), self.meta_content)

    def test_extract_xml_entry(self):
        key = f"xml_key_{self.random_prefix}"
        val = f"xml_val_{uuid.uuid4().hex[:8]}"
        markup = f'<data><entry key="{key}" value="{val}" /></data>'
        res = self.tool.extract(markup)
        self.assertEqual(res.get(key), val)

    def test_extract_json_script_block(self):
        payload = {self.json_key: self.json_val}
        markup = f'<div><script type="application/json">{json.dumps(payload)}</script></div>'
        res = self.tool.extract(markup)
        self.assertEqual(res.get(self.json_key), self.json_val)

    def test_extract_malformed_json_block(self):
        malformed_json = f'{{ "{self.json_key}": "{self.json_val}'
        markup = f'<div><script type="application/json">{malformed_json}</script></div>'
        res = self.tool.extract(markup)
        self.assertNotIn(self.json_key, res)

    def test_extract_frontmatter(self):
        markup = f"---\n{self.fm_key}: \"{self.fm_val}\"\n---\nBody text"
        res = self.tool.extract(markup)
        self.assertEqual(res.get(self.fm_key), self.fm_val)

    def test_extract_metadata_from_markup_method(self):
        markup = f'<meta property="{self.meta_name}" content="{self.meta_content}">'
        res = self.tool.extract_metadata_from_markup(markup)
        self.assertEqual(res.get(self.meta_name), self.meta_content)

    def test_top_level_functions(self):
        markup = f'<meta name="{self.meta_name}" content="{self.meta_content}">'
        res1 = extract_metadata(markup)
        res2 = extract(markup)
        self.assertEqual(res1.get(self.meta_name), self.meta_content)
        self.assertEqual(res2.get(self.meta_name), self.meta_content)

    def test_generate_extraction_report(self):
        prefix = f"test_report_{self.random_prefix}"
        markup = f'<meta name="{self.meta_name}" content="{self.meta_content}">'
        self.report_path = self.tool.generate_extraction_report(markup, prefix)
        self.assertTrue(os.path.exists(self.report_path))
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Extraction Report", content)
        self.assertIn(self.meta_name, content)


if __name__ == "__main__":
    unittest.main()
