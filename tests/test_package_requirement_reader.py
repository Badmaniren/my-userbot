import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string
from skills.package_requirement_reader import PyPIClient

class TestPackageRequirementReader(unittest.TestCase):
    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string.ascii_lowercase, k=8))
        self.base_url = f"https://{self.rand_str()}.org/pypi"
        self.client = PyPIClient(base_url=self.base_url)

    def test_get_package_metadata_success(self):
        pkg_name = self.rand_str()
        version = f"{random.randint(0, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        expected_meta = {
            "info": {
                "name": pkg_name,
                "version": version,
                "summary": self.rand_str()
            },
            "urls": []
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_meta
            mock_get.return_value = mock_response

            result = self.client.get_package_metadata(pkg_name, version)
            
            self.assertEqual(result.get("info", {}).get("name"), pkg_name)
            self.assertEqual(result.get("info", {}).get("version"), version)
            mock_get.assert_called_once()

    def test_get_package_metadata_failure(self):
        pkg_name = self.rand_str()
        version = f"{random.randint(0, 5)}.{random.randint(0, 9)}"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            result = self.client.get_package_metadata(pkg_name, version)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result, {})

    def test_get_release_versions(self):
        pkg_name = self.rand_str()
        versions = [f"{random.randint(1, 3)}.{random.randint(0, 5)}.0" for _ in range(3)]
        mock_data = {
            "releases": {v: [] for v in versions}
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response

            res = self.client.get_release_versions(pkg_name)
            self.assertTrue(all(v in res for v in versions))

    def test_get_dependencies(self):
        pkg_name = self.rand_str()
        version = f"1.{random.randint(0,9)}.0"
        deps = [f"{self.rand_str()} (>=1.0.0)", f"{self.rand_str()} (<2.0)"]
        mock_data = {
            "info": {
                "requires_dist": deps
            }
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response

            result = self.client.get_dependencies(pkg_name, version)
            self.assertEqual(result, deps)

    def test_get_package_dependencies_alias(self):
        pkg_name = self.rand_str()
        version = f"2.{random.randint(0,9)}.0"
        deps = [f"{self.rand_str()}==3.1.4"]
        mock_data = {
            "info": {
                "requires_dist": deps
            }
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response

            result = self.client.get_package_dependencies(pkg_name, version)
            self.assertEqual(result, deps)

    def test_parse_stream_data_valid(self):
        unique_key = uuid.uuid4().hex
        unique_val = self.rand_str()
        payload = json.dumps({unique_key: unique_val}).encode('utf-8')
        stream = io.BytesIO(payload)

        parsed = self.client.parse_stream_data(stream)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed.get(unique_key), unique_val)

    def test_parse_stream_data_invalid(self):
        garbage = f"{self.rand_str()} {{{self.rand_str()}".encode('utf-8')
        stream = io.BytesIO(garbage)

        parsed = self.client.parse_stream_data(stream)
        self.assertIsNone(parsed)

if __name__ == '__main__':
    unittest.main()