import unittest
import unittest.mock
import io
import uuid
import random
import string
from skills.extractor_tool_1791903203 import MetadataExtractor

class TestMetadataExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = MetadataExtractor()

    def test_extract_metadata_success(self):
        random_id = uuid.uuid4().hex
        random_key = ''.join(random.choices(string.ascii_letters, k=10))
        random_val = ''.join(random.choices(string.digits, k=8))

        mock_html = f"<html><meta name='{random_key}' content='{random_val}'><data id='{random_id}'></data></html>".encode('utf-8')

        with unittest.mock.patch('requests.get') as mock_get:
            mock_response = unittest.mock.Mock()
            mock_response.content = mock_html
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            random_url = f"https://{uuid.uuid4().hex}.com"
            result = self.extractor.extract(random_url)

            self.assertEqual(result.get(random_key), random_val)
            self.assertEqual(result.get('id'), random_id)

    def test_extract_metadata_malformed_input(self):
        random_garbage = bytes([random.randint(0, 255) for _ in range(64)])

        with unittest.mock.patch('requests.get') as mock_get:
            mock_response = unittest.mock.Mock()
            mock_response.content = random_garbage
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            random_url = f"http://{uuid.uuid4().hex}.internal"
            result = self.extractor.extract(random_url)

            self.assertIsInstance(result, dict)
            self.assertEqual(len(result), 0)

    def test_extract_metadata_connection_error(self):
        with unittest.mock.patch('requests.get', side_effect=Exception("Connection Failed")):
            random_url = f"https://{uuid.uuid4().hex}.net"

            with self.assertRaises(Exception):
                self.extractor.extract(random_url)

    def test_extract_metadata_empty_response(self):
        with unittest.mock.patch('requests.get') as mock_get:
            mock_response = unittest.mock.Mock()
            mock_response.content = b""
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            random_url = f"https://{uuid.uuid4().hex}.org"
            result = self.extractor.extract(random_url)

            self.assertEqual(result, {})

    def test_extract_metadata_complex_structure(self):
        random_tags = {f"attr_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex for _ in range(5)}
        html_content = "<html>" + "".join([f"<meta name='{k}' content='{v}'>" for k, v in random_tags.items()]) + "</html>"

        with unittest.mock.patch('requests.get') as mock_get:
            mock_response = unittest.mock.Mock()
            mock_response.content = html_content.encode('utf-8')
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            random_url = f"https://{uuid.uuid4().hex}.io"
            result = self.extractor.extract(random_url)

            for k, v in random_tags.items():
                self.assertEqual(result.get(k), v)

if __name__ == '__main__':
    unittest.main()