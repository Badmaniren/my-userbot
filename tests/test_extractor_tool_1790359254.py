import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string
from skills.extractor_tool_1790359254 import MetadataExtractor

class TestMetadataExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = MetadataExtractor()

    def test_extract_metadata_success(self):
        random_id = uuid.uuid4().hex
        random_key = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_val = ''.join(random.choices(string.digits, k=8))

        html_content = f"<html><body><div id='{random_id}' data-{random_key}='{random_val}'></div></body></html>"
        mock_response = MagicMock()
        mock_response.text = html_content

        with patch('requests.get', return_value=mock_response):
            random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=5))}.com/{uuid.uuid4().hex}"
            result = self.extractor.extract(random_url)

            self.assertEqual(result.get(random_key), random_val)
            self.assertEqual(result.get('id'), random_id)

    def test_extract_metadata_invalid_markup(self):
        random_garbage = ''.join(random.choices(string.printable, k=50))
        mock_response = MagicMock()
        mock_response.text = random_garbage

        with patch('requests.get', return_value=mock_response):
            random_url = f"https://{uuid.uuid4().hex}.io"
            result = self.extractor.extract(random_url)

            self.assertIsInstance(result, dict)
            self.assertEqual(len(result), 0)

    def test_extract_metadata_network_failure(self):
        with patch('requests.get', side_effect=Exception("Connection Timeout")):
            random_url = f"http://{uuid.uuid4().hex}.net"
            with self.assertRaises(Exception) as context:
                self.extractor.extract(random_url)
            self.assertTrue("Connection Timeout" in str(context.exception))

    def test_stream_processing_integrity(self):
        random_bytes = bytes([random.randint(0, 255) for _ in range(1024)])
        mock_stream = io.BytesIO(random_bytes)

        with patch('bs4.BeautifulSoup') as mock_bs:
            instance = mock_bs.return_value
            instance.find.return_value = None

            result = self.extractor.process_stream(mock_stream)
            self.assertIsNone(result)
            mock_bs.assert_called_once()

    def test_metadata_mapping_logic(self):
        random_keys = [uuid.uuid4().hex for _ in range(3)]
        random_vals = [str(random.randint(1000, 9999)) for _ in range(3)]

        mock_soup = MagicMock()
        mock_elements = []
        for k, v in zip(random_keys, random_vals):
            el = MagicMock()
            el.attrs = {k: v}
            mock_elements.append(el)

        mock_soup.find_all.return_value = mock_elements

        result = self.extractor._map_elements(mock_soup)

        for i in range(3):
            self.assertEqual(result[random_keys[i]], random_vals[i])

if __name__ == '__main__':
    unittest.main()
