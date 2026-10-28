import unittest
import uuid
import random
import string
import io
from unittest.mock import MagicMock, patch
from skills.extractor_tool_1793210610 import ExtractorTool

class TestExtractorTool(unittest.TestCase):
    def setUp(self):
        self.tool = ExtractorTool()

    def _generate_random_markup(self):
        tag = ''.join(random.choices(string.ascii_lowercase, k=8))
        attr_key = ''.join(random.choices(string.ascii_lowercase, k=5))
        attr_val = uuid.uuid4().hex
        content = uuid.uuid4().hex
        return f"<{tag} {attr_key}='{attr_val}'>{content}</{tag}>", attr_key, attr_val, content

    def test_extract_metadata_integrity(self):
        markup, attr_key, attr_val, content = self._generate_random_markup()

        result = self.tool.extract(markup)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get(attr_key), attr_val)
        self.assertEqual(result.get('content'), content)

    def test_parse_attributes_randomized(self):
        key1, val1 = uuid.uuid4().hex, uuid.uuid4().hex
        key2, val2 = uuid.uuid4().hex, uuid.uuid4().hex
        tag_string = f'{key1}="{val1}" {key2}="{val2}"'

        result = self.tool.parse_attributes(tag_string)

        self.assertEqual(result.get(key1), val1)
        self.assertEqual(result.get(key2), val2)
        self.assertEqual(len(result), 2)

    def test_extract_with_malformed_input(self):
        random_garbage = uuid.uuid4().hex
        with self.assertRaises(Exception):
            self.tool.extract(random_garbage)

    def test_mocked_stream_processing(self):
        # Имитация чтения из потока данных
        mock_stream = MagicMock()
        random_data = f"<{uuid.uuid4().hex} id='{uuid.uuid4().hex}'>data</{uuid.uuid4().hex}>"
        mock_stream.read.return_value = random_data

        data = mock_stream.read()
        result = self.tool.extract(data)

        self.assertIn('id', result)
        self.assertEqual(result['content'], 'data')

    def test_edge_case_empty_attributes(self):
        tag_name = uuid.uuid4().hex
        markup = f"<{tag_name}></{tag_name}>"

        result = self.tool.extract(markup)

        self.assertEqual(result.get('tag'), tag_name)
        self.assertEqual(result.get('content'), '')

    def test_complex_attribute_parsing(self):
        attr_map = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(5)}
        attr_string = " ".join([f'{k}="{v}"' for k, v in attr_map.items()])

        result = self.tool.parse_attributes(attr_string)

        for k, v in attr_map.items():
            self.assertEqual(result[k], v)

if __name__ == '__main__':
    unittest.main()