import unittest
import uuid
import random
import json
from skills.extractor_tool_1790102839 import ExtractorTool, extract_metadata


class TestExtractorTool1790102839(unittest.TestCase):

    def setUp(self) -> None:
        self.tool = ExtractorTool()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.meta_name = f"meta_{self.random_prefix}"
        self.meta_content = f"content_{uuid.uuid4().hex[:8]}"
        self.json_key = f"key_{self.random_prefix}"
        self.json_val = f"val_{uuid.uuid4().hex[:8]}"
        self.fm_key = f"fm_{self.random_prefix}"
        self.fm_val = f"val_fm_{uuid.uuid4().hex[:8]}"

    def test_extract_invalid_input(self) -> None:
        invalid_inputs = [
            None,
            12345,
            ["some", "markup"],
            {"markup": "data"},
            123.45,
            True
        ]
        for item in invalid_inputs:
            with self.subTest(item=item):
                res = self.tool.extract(item)
                self.assertEqual(res, {})

    def test_extract_meta_tags(self) -> None:
        markup = f'<html><head><meta name="{self.meta_name}" content="{self.meta_content}"></head></html>'
        res = self.tool.extract(markup)
        self.assertIn(self.meta_name, res)
        self.assertEqual(res[self.meta_name], self.meta_content)

    def test_extract_json_block(self) -> None:
        payload = {self.json_key: self.json_val}
        markup = f'<div><script type="application/json">{json.dumps(payload)}</script></div>'
        res = self.tool.extract(markup)
        self.assertIn(self.json_key, res)
        self.assertEqual(res[self.json_key], self.json_val)

    def test_extract_malformed_json_block(self) -> None:
        malformed_json = f'{{ "{self.json_key}": "{self.json_val}'
        markup = f'<div><script type="application/json">{malformed_json}</script></div>'
        res = self.tool.extract(markup)
        self.assertNotIn(self.json_key, res)

    def test_extract_frontmatter(self) -> None:
        markup = f"---\n{self.fm_key}: \"{self.fm_val}\"\n---\nSome body text here {uuid.uuid4().hex}"
        res = self.tool.extract(markup)
        self.assertIn(self.fm_key, res)
        self.assertEqual(res[self.fm_key], self.fm_val)

    def test_extract_combined_markup(self) -> None:
        payload = {self.json_key: self.json_val}
        markup = f"""---
{self.fm_key}: {self.fm_val}
---
<html>
<head>
<meta name="{self.meta_name}" content="{self.meta_content}">
</head>
<body>
<script type="application/json">
{json.dumps(payload)}
</script>
</body>
</html>
"""
        res = self.tool.extract(markup)
        self.assertEqual(res.get(self.fm_key), self.fm_val)
        self.assertEqual(res.get(self.meta_name), self.meta_content)
        self.assertEqual(res.get(self.json_key), self.json_val)

    def test_helper_function(self) -> None:
        markup = f'<meta name="{self.meta_name}" content="{self.meta_content}">'
        res = extract_metadata(markup)
        self.assertIn(self.meta_name, res)
        self.assertEqual(res[self.meta_name], self.meta_content)


if __name__ == "__main__":
    unittest.main()