import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from bs4 import BeautifulSoup

from skills.extractor_tool_1790270493 import (
    ExtractorTool1790270493,
    ExtractionError
)


class TestExtractorTool1790270493(unittest.TestCase):

    def setUp(self):
        self.tool = ExtractorTool1790270493()
        self.random_tag = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_attr = ''.join(random.choices(string.ascii_lowercase, k=6))
        self.random_value = str(uuid.uuid4())

    def test_extract_metadata_success(self):
        html_content = f'<{self.random_tag} {self.random_attr}="{self.random_value}">Random text content {uuid.uuid4().hex}</{self.random_tag}>'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_response.text = html_content

        target_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=10))}.org/{uuid.uuid4().hex}"

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.tool.extract_from_url(target_url, self.random_tag, self.random_attr)

            mock_get.assert_called_once_with(target_url, timeout=10)
            self.assertIsInstance(result, dict)
            self.assertIn(self.random_attr, result)
            self.assertEqual(result[self.random_attr], self.random_value)

    def test_extract_metadata_from_stream_random_bytes(self):
        stream_id = uuid.uuid4().hex
        noise_bytes = f'<meta name="{self.random_attr}" content="{stream_id}">'.encode('utf-8')
        mock_stream = io.BytesIO(noise_bytes)

        result = self.tool.extract_from_stream(mock_stream, "meta", "name")

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get(self.random_attr), stream_id)

    def test_extract_metadata_network_failure(self):
        bad_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=12))}.local/{uuid.uuid4().hex}"

        with patch('requests.get', side_effect=Exception(uuid.uuid4().hex)) as mock_get:
            with self.assertRaises(ExtractionError):
                self.tool.extract_from_url(bad_url, self.random_tag, self.random_attr)
            mock_get.assert_called_once()

    def test_extract_missing_attribute_resilience(self):
        missing_val = uuid.uuid4().hex
        html_content = f'<{self.random_tag} other_attr="{missing_val}">No target attribute here</{self.random_tag}>'

        mock_stream = io.BytesIO(html_content.encode('utf-8'))
        result = self.tool.extract_from_stream(mock_stream, self.random_tag, self.random_attr)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_multiple_elements_extraction(self):
        val_one = uuid.uuid4().hex
        val_two = uuid.uuid4().hex

        html_content = (
            f'<div class="{self.random_attr}" data-id="{val_one}">First</div>'
            f'<div class="{self.random_attr}" data-id="{val_two}">Second</div>'
        )

        mock_stream = io.BytesIO(html_content.encode('utf-8'))
        results = self.tool.extract_all_from_stream(mock_stream, "div", "data-id")

        self.assertIsInstance(results, list)
        self.assertIn(val_one, results)
        self.assertIn(val_two, results)
        self.assertEqual(len(results), 2)


if __name__ == '__main__':
    unittest.main()