import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.dependency_parser import parse_dependency, DependencyParser

class TestDependencyParserInquisitorial(unittest.TestCase):

    def setUp(self):
        self.random_pkg = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(0, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_marker = f"python_version < '{random.choice([3.7, 3.8, 3.9])}'"

    def test_parse_simple_dependency_string(self):
        raw_dep = f"{self.random_pkg} >= {self.random_version}"
        result = parse_dependency(raw_dep)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("name"), self.random_pkg)
        self.assertIn(">=", str(result.get("specifier")))
        self.assertIn(self.random_version, str(result.get("specifier")))

    def test_parse_dependency_with_markers(self):
        raw_dep = f"{self.random_pkg} (=={self.random_version}); {self.random_marker}"
        result = parse_dependency(raw_dep)

        self.assertEqual(result.get("name"), self.random_pkg)
        self.assertEqual(result.get("marker"), self.random_marker)

    def test_parser_class_stream_handling(self):
        random_stream_content = f"{self.random_pkg}=={self.random_version}\n".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_content)

        parser = DependencyParser()
        parsed_list = parser.parse_stream(mock_stream)

        self.assertIsInstance(parsed_list, list)
        self.assertTrue(len(parsed_list) > 0)
        self.assertEqual(parsed_list[0].get("name"), self.random_pkg)

    def test_parse_invalid_pep508_string_raises(self):
        invalid_str = "".join(random.choices(string.punctuation, k=10))
        parser = DependencyParser()

        with self.assertRaises(Exception):
            parser.parse_string(invalid_str)

    def test_dependency_parser_extra_fields(self):
        extra_name = f"extra-{uuid.uuid4().hex[:4]}"
        raw_dep = f"{self.random_pkg}[{extra_name}] ~= {self.random_version}"

        result = parse_dependency(raw_dep)
        self.assertEqual(result.get("name"), self.random_pkg)
        self.assertIn(extra_name, result.get("extras", []))

    def test_mocked_pypi_client_dependency_parsing(self):
        mock_response_data = {
            "info": {
                "requires_dist": [
                    f"{self.random_pkg} >= {self.random_version}",
                    f"requests>=2.0.0"
                ]
            }
        }

        with patch('skills.pypi_client.requests.get') as mock_get:
            mock_instance = MagicMock()
            mock_instance.status_code = 200
            mock_instance.json.return_value = mock_response_data
            mock_get.return_value = mock_instance

            parser = DependencyParser()
            dependencies = parser.fetch_and_parse(self.random_pkg, self.random_version)

            self.assertIsInstance(dependencies, list)
            self.assertEqual(len(dependencies), 2)
            found_target = any(d.get("name") == self.random_pkg for d in dependencies)
            self.assertTrue(found_target)

    def test_parse_stream_data_with_garbage(self):
        garbage_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(garbage_bytes)

        parser = DependencyParser()
        result = parser.parse_stream(mock_stream)

        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()