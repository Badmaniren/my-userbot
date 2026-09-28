import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.extractor_tool_1790558131 import extract_metadata, extractor_tool_1790558131

class TestExtractorTool1790558131(unittest.TestCase):

    def test_extract_metadata_success_url(self):
        rand_name = f"name_{uuid.uuid4().hex[:8]}"
        rand_content = f"content_{uuid.uuid4().hex[:8]}"
        rand_url = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:8]}"

        html_content = f'<html><head><meta name="{rand_name}" content="{rand_content}"></head></html>'

        mock_response = MagicMock()
        mock_response.content = html_content.encode('utf-8')

        with patch('skills.extractor_tool_1790558131.requests.get', return_value=mock_response) as mock_get:
            result = extract_metadata(rand_url, from_file=False)
            mock_get.assert_called_once_with(rand_url, timeout=10)
            self.assertIn(rand_name, result)
            self.assertEqual(result[rand_name], rand_content)

    def test_extract_metadata_success_file(self):
        rand_prop = f"prop_{uuid.uuid4().hex[:8]}"
        rand_val = f"val_{uuid.uuid4().hex[:8]}"
        rand_path = f"/tmp/{uuid.uuid4().hex[:8]}.html"

        html_content = f'<html><head><meta property="{rand_prop}" content="{rand_val}"></head></html>'

        mock_file = io.BytesIO(html_content.encode('utf-8'))

        with patch('builtins.open', return_value=mock_file) as mock_open:
            result = extract_metadata(rand_path, from_file=True)
            mock_open.assert_called_once_with(rand_path, 'rb')
            self.assertIn(rand_prop, result)
            self.assertEqual(result[rand_prop], rand_val)

    def test_extract_metadata_exception_handling(self):
        rand_err_url = f"https://{uuid.uuid4().hex[:8]}.invalid"
        rand_err_msg = f"error_{uuid.uuid4().hex[:8]}"

        with patch('skills.extractor_tool_1790558131.requests.get', side_effect=Exception(rand_err_msg)) as mock_get:
            result = extract_metadata(rand_err_url, from_file=False)
            mock_get.assert_called_once_with(rand_err_url, timeout=10)
            self.assertIn('error', result)
            self.assertEqual(result['error'], rand_err_msg)

    def test_extractor_tool_dictionary_input(self):
        rand_dict = {
            f"key_{uuid.uuid4().hex[:6]}": f"val_{uuid.uuid4().hex[:6]}",
            f"key_{uuid.uuid4().hex[:6]}": f"val_{uuid.uuid4().hex[:6]}"
        }
        result = extractor_tool_1790558131(rand_dict)
        self.assertEqual(result, rand_dict)

    def test_extractor_tool_html_with_ids(self):
        rand_id1 = f"id_{uuid.uuid4().hex[:6]}"
        rand_text1 = f"text_{uuid.uuid4().hex[:6]}"
        rand_id2 = f"id_{uuid.uuid4().hex[:6]}"
        rand_text2 = f"text_{uuid.uuid4().hex[:6]}"

        html_data = f'<div><span id="{rand_id1}">{rand_text1}</span><p id="{rand_id2}">{rand_text2}</p></div>'

        result = extractor_tool_1790558131(html_data)
        self.assertIn(rand_id1, result)
        self.assertEqual(result[rand_id1], rand_text1)
        self.assertIn(rand_id2, result)
        self.assertEqual(result[rand_id2], rand_text2)

    def test_extractor_tool_fallback_content(self):
        rand_plain_text = f"plain_content_{uuid.uuid4().hex[:8]}"
        html_data = f'<html><body><div>{rand_plain_text}</div></body></html>'

        result = extractor_tool_1790558131(html_data)
        self.assertIn('content', result)
        self.assertIn(rand_plain_text, result['content'])

if __name__ == '__main__':
    unittest.main()