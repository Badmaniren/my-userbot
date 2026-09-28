import unittest
from skills.extractor_tool_1790630083 import extract_metadata, ExtractorTool


class TestExtractorUnit(unittest.TestCase):
    def setUp(self):
        self.extractor = ExtractorTool()

    def test_basic_extraction(self):
        html = "<html><head><meta name='ticker' content='AAPL'></head><body></body></html>"
        result = extract_metadata(html)
        self.assertEqual(result.get('ticker'), 'AAPL')
        self.assertEqual(self.extractor.extract(html).get('ticker'), 'AAPL')

    def test_multiple_meta_tags(self):
        html = """
        <html>
            <meta name='author' content='Ungu'>
            <meta name='version' content='1.0'>
        </html>
        """
        result = extract_metadata(html)
        self.assertEqual(result, {'author': 'Ungu', 'version': '1.0'})

    def test_malformed_html(self):
        html = "<meta name='test' content='val'>"
        result = extract_metadata(html)
        self.assertEqual(result, {'test': 'val'})

    def test_no_meta_tags(self):
        html = "<html><body><h1>No meta here</h1></body></html>"
        result = extract_metadata(html)
        self.assertEqual(result, {})

    def test_empty_or_invalid_input(self):
        self.assertEqual(extract_metadata(""), {})
        self.assertEqual(extract_metadata(None), {})


if __name__ == '__main__':
    unittest.main()
