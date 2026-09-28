import unittest
import uuid
import random
import os
from skills.extractor_tool_1790558131 import extractor_tool_1790558131, extract_metadata
from skills.market_parser import MarketParser

class TestIntegrationExtractorTool1790558131(unittest.TestCase):

    def setUp(self):
        self.random_id = f"id_{uuid.uuid4().hex[:8]}"
        self.random_text = f"content_{uuid.uuid4().hex}"
        self.test_filename = f"test_meta_{uuid.uuid4().hex}.html"

        html_content = f'<html><head><meta name="description" content="{self.random_text}"></head><body><div id="{self.random_id}">{self.random_text}</div></body></html>'

        with open(self.test_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.html_content = html_content

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_integration_extractor_with_file_and_market_parser(self):
        metadata = extract_metadata(self.test_filename, from_file=True)
        self.assertIn('description', metadata)
        self.assertEqual(metadata['description'], self.random_text)

        extraction_result = extractor_tool_1790558131(self.html_content)
        self.assertIn(self.random_id, extraction_result)
        self.assertEqual(extraction_result[self.random_id], self.random_text)

        parser = MarketParser()
        self.assertIsNotNone(parser)

if __name__ == '__main__':
    unittest.main()