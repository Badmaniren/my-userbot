import unittest
import uuid
import random
from skills.extractor_tool_1789544538 import extract_metadata

class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex
        self.random_suffix = random.randint(1000, 9999)

    def test_extract_metadata_from_html_markup(self):
        expected_title = f"Title-{self.unique_id}-{self.random_suffix}"
        expected_author = f"Author-{self.unique_id}"
        expected_description = f"Description-{self.random_suffix}"
        custom_key = f"custom_key_{self.random_suffix}"
        custom_value = f"custom_value_{self.unique_id}"

        html_markup = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{expected_title}</title>
            <meta name="author" content="{expected_author}">
            <meta name="description" content="{expected_description}">
            <meta name="{custom_key}" content="{custom_value}">
        </head>
        <body>
            <h1>Integration Test Content</h1>
        </body>
        </html>
        """

        extracted_data = extract_metadata(html_markup)

        self.assertIsInstance(extracted_data, dict, "Extractor must return a dictionary")
        self.assertEqual(extracted_data.get("title"), expected_title, "Failed to extract title")
        self.assertEqual(extracted_data.get("author"), expected_author, "Failed to extract author")
        self.assertEqual(extracted_data.get("description"), expected_description, "Failed to extract description")
        self.assertEqual(extracted_data.get(custom_key), custom_value, "Failed to extract custom meta tag")

    def test_extract_metadata_empty_markup(self):
        empty_markup = ""
        extracted_data = extract_metadata(empty_markup)
        self.assertIsInstance(extracted_data, dict)
        self.assertEqual(len(extracted_data), 0, "Empty markup should yield empty metadata dictionary")

if __name__ == "__main__":
    unittest.main()