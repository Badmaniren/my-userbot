import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from io import BytesIO
from skills.dependency_parser import parse_dependency, DependencyParser

class TestDependencyParser(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.random_pkg_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_marker = f"python_version < '{random.randint(3, 4)}.{random.randint(0, 9)}'"

    def test_parse_simple_dependency_string(self):
        req_string = f"{self.random_pkg_name} (>={self.random_version})"
        result = parse_dependency(req_string)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('name'), self.random_pkg_name)
        self.assertIn(self.random_version, result.get('constraints', ''))

    def test_parse_dependency_with_extras_and_markers(self):
        extra_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        req_string = f"{self.random_pkg_name}[{extra_name}] == {self.random_version}; {self.random_marker}"
        result = self.parser.parse(req_string)
        self.assertEqual(result.get('name'), self.random_pkg_name)
        self.assertIn(extra_name, result.get('extras', []))
        self.assertEqual(result.get('marker'), self.random_marker)

    def test_parse_stream_data_with_dependencies(self):
        stream_content = f"{self.random_pkg_name}=={self.random_version}\n".encode('utf-8')
        mock_stream = BytesIO(stream_content)
        
        result = self.parser.parse_stream(mock_stream)
        self.assertIsInstance(result, list)
        self.assertTrue(any(item.get('name') == self.random_pkg_name for item in result))

    def test_invalid_dependency_format(self):
        garbage_string = uuid.uuid4().hex
        result = parse_dependency(garbage_string)
        self.assertIsNone(result.get('constraints'))

    def test_parser_with_mocked_external_call(self):
        target_url = f"https://{uuid.uuid4().hex}.pypi.io/pypi/{self.random_pkg_name}/json"
        mock_response_data = {
            "info": {
                "requires_dist": [
                    f"{self.random_pkg_name} (>= {self.random_version})"
                ]
            }
        }
        
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp
            
            deps = self.parser.fetch_and_parse(target_url)
            self.assertIn(self.random_pkg_name, [d['name'] for d in deps])
            mock_get.assert_called_once_with(target_url)

if __name__ == '__main__':
    unittest.main()