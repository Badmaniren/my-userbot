import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.pypi_client import PyPIClient

class TestPyPIClientUnit(unittest.TestCase):
    def setUp(self):
        self.random_base = f"https://{uuid.uuid4().hex}.org/api"
        self.client = PyPIClient(base_url=self.random_base)
        self.pkg_name = f"pkg_{uuid.uuid4().hex[:8]}"
        self.version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    @patch('skills.pypi_client.requests.get')
    def test_get_package_metadata_success(self, mock_get):
        expected_data = {
            "info": {
                "name": self.pkg_name,
                "version": self.version,
                "requires_dist": [f"dep_{uuid.uuid4().hex} (>=1.0.0)"]
            },
            "releases": {
                self.version: []
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        result = self.client.get_package_metadata(self.pkg_name, self.version)
        
        mock_get.assert_called_once_with(f"{self.random_base}/{self.pkg_name}/{self.version}/json")
        self.assertEqual(result, expected_data)

    @patch('skills.pypi_client.requests.get')
    def test_get_package_metadata_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.client.get_package_metadata(self.pkg_name)
        
        mock_get.assert_called_once_with(f"{self.random_base}/{self.pkg_name}/json")
        self.assertIsNone(result)

    @patch('skills.pypi_client.requests.get')
    def test_get_release_versions(self, mock_get):
        versions = [f"1.0.{random.randint(0, 5)}", f"2.0.{random.randint(0, 5)}"]
        expected_data = {
            "releases": {
                versions[0]: [],
                versions[1]: []
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        result = self.client.get_release_versions(self.pkg_name)
        
        self.assertIn(versions[0], result)
        self.assertIn(versions[1], result)
        self.assertEqual(len(result), 2)

    @patch('skills.pypi_client.requests.get')
    def test_get_release_versions_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = self.client.get_release_versions(self.pkg_name)
        self.assertEqual(result, [])

    @patch('skills.pypi_client.requests.get')
    def test_get_dependencies(self, mock_get):
        dep_name = f"dependency_{uuid.uuid4().hex[:6]}"
        expected_data = {
            "info": {
                "requires_dist": [dep_name]
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        result = self.client.get_dependencies(self.pkg_name, self.version)
        
        self.assertEqual(result, [dep_name])

    @patch('skills.pypi_client.requests.get')
    def test_get_dependencies_missing(self, mock_get):
        expected_data = {
            "info": {}
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        result = self.client.get_dependencies(self.pkg_name)
        self.assertEqual(result, [])

    @patch('skills.pypi_client.requests.get')
    def test_get_package_dependencies_raises(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client.get_package_dependencies(self.pkg_name, self.version)

    @patch('skills.pypi_client.requests.get')
    def test_get_package_dependencies_success(self, mock_get):
        dep_name = f"lib_{uuid.uuid4().hex[:5]}"
        expected_data = {
            "info": {
                "requires_dist": [dep_name]
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        result = self.client.get_package_dependencies(self.pkg_name)
        self.assertEqual(result, [dep_name])

    def test_parse_stream_data_valid(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        payload = json.dumps({random_key: random_val}).encode('utf-8')
        stream = io.BytesIO(payload)

        result = self.client.parse_stream_data(stream)
        self.assertEqual(result.get(random_key), random_val)

    def test_parse_stream_data_invalid(self):
        invalid_payload = b"{malformed_json"
        stream = io.BytesIO(invalid_payload)

        result = self.client.parse_stream_data(stream)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()