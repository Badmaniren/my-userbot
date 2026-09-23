import os
import random
import string
import tempfile
import unittest
import uuid

import skills.extractor_tool_1790183859 as extractor


def generate_random_str(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class TestExtractorTool1790183859Integration(unittest.TestCase):

    def setUp(self):
        self.dynamic_uuid = str(uuid.uuid4())
        self.random_author = f"author_{generate_random_str(8)}"
        self.random_category = f"cat_{generate_random_str(6)}"
        self.random_metric = random.randint(1000, 999999)

    def test_extract_metadata_from_html_markup(self):
        random_title = f"Title_{generate_random_str(10)}"

        html_markup = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="title" content="{random_title}">
            <meta name="author" content="{self.random_author}">
            <meta name="doc_id" content="{self.dynamic_uuid}">
            <meta name="category" content="{self.random_category}">
            <meta name="metric" content="{self.random_metric}">
        </head>
        <body>
            <h1>Integration Test Document</h1>
        </body>
        </html>
        """

        result = extractor.extract_metadata(html_markup)

        self.assertIsInstance(result, dict)
        self.assertIn("metadata", result)

        extracted_meta = result["metadata"]
        self.assertEqual(extracted_meta.get("title"), random_title)
        self.assertEqual(extracted_meta.get("author"), self.random_author)
        self.assertEqual(extracted_meta.get("doc_id"), self.dynamic_uuid)
        self.assertEqual(extracted_meta.get("category"), self.random_category)
        self.assertEqual(str(extracted_meta.get("metric")), str(self.random_metric))

    def test_extract_metadata_from_file_and_persistence(self):
        custom_key = f"key_{generate_random_str(6)}"
        custom_val = f"val_{generate_random_str(16)}"
        file_uuid = str(uuid.uuid4())

        markup_data = f"""---
doc_id: {file_uuid}
{custom_key}: {custom_val}
status: active
---
# Content Header
Dynamic body with UUID {file_uuid}
"""

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".md", encoding="utf-8") as tmp_file:
            tmp_filepath = tmp_file.name
            tmp_file.write(markup_data)

        try:
            self.assertTrue(os.path.exists(tmp_filepath))

            result = extractor.extract_metadata_from_file(tmp_filepath)

            self.assertIsInstance(result, dict)
            self.assertIn("metadata", result)

            meta = result["metadata"]
            self.assertEqual(meta.get("doc_id"), file_uuid)
            self.assertEqual(meta.get(custom_key), custom_val)
            self.assertEqual(meta.get("status"), "active")
            self.assertEqual(result.get("source_file"), tmp_filepath)

        finally:
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)

    def test_extract_structured_comment_markup(self):
        token_id = str(uuid.uuid4())
        secret_code = generate_random_str(24)

        comment_markup = f"""
        <!-- metadata: {{"token_id": "{token_id}", "secret_code": "{secret_code}", "score": {self.random_metric}}} -->
        <div>
            <p>Embedded metadata test</p>
        </div>
        """

        result = extractor.extract_metadata(comment_markup)

        self.assertIsInstance(result, dict)
        self.assertIn("metadata", result)

        meta = result["metadata"]
        self.assertEqual(meta.get("token_id"), token_id)
        self.assertEqual(meta.get("secret_code"), secret_code)
        self.assertEqual(int(meta.get("score")), self.random_metric)


if __name__ == "__main__":
    unittest.main()