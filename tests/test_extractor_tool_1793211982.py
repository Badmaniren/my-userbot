import unittest
from skills.extractor_tool_1793211982 import ExtractorTool


class TestExtractorTool(unittest.TestCase):
    def setUp(self):
        self.extractor = ExtractorTool()

    def test_init(self):
        self.assertEqual(self.extractor.version, "1.0.0")

    def test_parse_attributes_valid(self):
        tag_str = '<metadata id="123" name="test" status=\'active\' />'
        attrs = self.extractor.parse_attributes(tag_str)
        self.assertEqual(attrs, {"id": "123", "name": "test", "status": "active"})

    def test_parse_attributes_empty_or_invalid(self):
        self.assertEqual(self.extractor.parse_attributes(""), {})
        self.assertEqual(self.extractor.parse_attributes(None), {})
        self.assertEqual(self.extractor.parse_attributes(123), {})

    def test_extract_xml_tags(self):
        markup = '<item id="abc" category="books"><title>Sample</title></item>'
        data = self.extractor.extract(markup)
        self.assertEqual(data.get("id"), "abc")
        self.assertEqual(data.get("category"), "books")

    def test_extract_key_value_lines(self):
        markup = "Title: Test Title\nAuthor: John Doe\n"
        data = self.extractor.extract(markup)
        self.assertEqual(data.get("title"), "Test Title")
        self.assertEqual(data.get("author"), "John Doe")

    def test_extract_combined(self):
        markup = '<meta key="val" />\nStatus: Active\n'
        data = self.extractor.extract(markup)
        self.assertEqual(data.get("key"), "val")
        self.assertEqual(data.get("status"), "Active")

    def test_extract_empty_or_invalid(self):
        self.assertEqual(self.extractor.extract(""), {})
        self.assertEqual(self.extractor.extract(None), {})
        self.assertEqual(self.extractor.extract(123), {})


if __name__ == "__main__":
    unittest.main()
