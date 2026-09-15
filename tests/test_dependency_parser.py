import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.dependency_parser import DependencyParser, parse_dependency, parse_dependency_string

class TestDependencyParser(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.random_pkg_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_version = f"{random.randint(1, 5)}.{random.randint(0, 9)}"
        self.random_extra = ''.join(random.choices(string.ascii_lowercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.pypi.org/pypi/{self.random_pkg_name}/json"

    def test_parse_valid_requirement(self):
        req_str = f"{self.random_pkg_name} >={self.random_version}"
        result = self.parser.parse(req_str)
        self.assertEqual(result['name'], self.random_pkg_name)
        self.assertIn(self.random_version, result['constraints'])
        self.assertEqual(result['version_constraint'], result['constraints'])
        self.assertEqual(result['extras'], [])
        self.assertIsNone(result['marker'])

    def test_parse_with_extras_and_marker(self):
        random_marker_env = ''.join(random.choices(string.ascii_lowercase, k=4))
        req_str = f"{self.random_pkg_name}[{self.random_extra}] >={self.random_version}; python_version < '{random_marker_env}'"
        result = self.parser.parse(req_str)
        self.assertEqual(result['name'], self.random_pkg_name)
        self.assertIn(self.random_extra, result['extras'])
        self.assertIsNotNone(result['marker'])

    def test_parse_fallback_on_invalid_requirement(self):
        invalid_req = f"invalid_req_format_{uuid.uuid4().hex[:6]}!@#"
        expected_name = invalid_req.split()[0]
        result = self.parser.parse(invalid_req)
        self.assertEqual(result['name'], expected_name)
        self.assertIsNone(result['constraints'])
        self.assertIsNone(result['version_constraint'])
        self.assertEqual(result['extras'], [])
        self.assertIsNone(result['marker'])

    def test_parse_stream(self):
        pkg1 = ''.join(random.choices(string.ascii_lowercase, k=6))
        pkg2 = ''.join(random.choices(string.ascii_lowercase, k=6))
        stream_data = f"# Comment line\n\n{pkg1}==1.0\n{pkg2}>=2.0\n".encode('utf-8')
        stream = io.BytesIO(stream_data)
        
        results = self.parser.parse_stream(stream)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], pkg1)
        self.assertEqual(results[1]['name'], pkg2)

    def test_fetch_and_parse(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "info": {
                "requires_dist": [
                    f"{self.random_pkg_name}=={self.random_version}",
                    f"another-pkg>=1.0"
                ]
            }
        }
        
        with patch('skills.dependency_parser.requests.get', return_value=mock_response) as mock_get:
            results = self.parser.fetch_and_parse(self.random_url)
            mock_get.assert_called_once_with(self.random_url)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['name'], self.random_pkg_name)

    def test_module_level_helpers(self):
        req_str = f"{self.random_pkg_name}=={self.random_version}"
        res1 = parse_dependency(req_str)
        res2 = parse_dependency_string(req_str)
        self.assertEqual(res1['name'], self.random_pkg_name)
        self.assertEqual(res2['name'], self.random_pkg_name)
        self.assertEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()