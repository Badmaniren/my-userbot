import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.pypi_client import PyPIClient

class TestPyPIClient(unittest.TestCase):
    def setUp(self):
        self.client = PyPIClient()
        self.random_package = ''.join(random.choices(string.ascii_lowercase, k=10)) + '_' + uuid.uuid4().hex[:6]
        self.random_version = f"{random.randint(0, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_summary = ''.join(random.choices(string.ascii_letters + ' ', k=30))

    def test_get_package_metadata_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "name": self.random_package,
                "version": self.random_version,
                "summary": self.random_summary
            },
            "releases": {
                self.random_version: []
            }
        }

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.client.get_package_metadata(self.random_package)
            
            self.assertIsNotNone(result)
            self.assertEqual(result["info"]["name"], self.random_package)
            self.assertEqual(result["info"]["version"], self.random_version)
            self.assertEqual(result["info"]["summary"], self.random_summary)
            mock_get.assert_called_once()
            self.assertIn(self.random_package, mock_get.call_args[0][0])

    def test_get_package_metadata_not_found(self):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.client.get_package_metadata(self.random_package)
            self.assertIsNone(result)
            mock_get.assert_called_once()

    def test_get_release_versions(self):
        version_list = [
            f"1.{random.randint(0, 9)}.{random.randint(0, 9)}",
            f"2.{random.randint(0, 9)}.{random.randint(0, 9)}",
            f"3.{random.randint(0, 9)}.{random.randint(0, 9)}"
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "releases": {v: [{"url": uuid.uuid4().hex}] for v in version_list}
        }

        with patch('requests.get', return_value=mock_response):
            versions = self.client.get_release_versions(self.random_package)
            self.assertIsInstance(versions, list)
            for v in version_list:
                self.assertIn(v, versions)

    def test_get_dependencies_success(self):
        dep_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "requires_dist": [
                    f"{dep_name} (>=1.0.0)",
                    f"{uuid.uuid4().hex[:5]} ; extra == 'dev'"
                ]
            }
        }

        with patch('requests.get', return_value=mock_response):
            dependencies = self.client.get_dependencies(self.random_package, self.random_version)
            self.assertIsInstance(dependencies, list)
            self.assertTrue(any(dep_name in d for d in dependencies))

    def test_get_dependencies_empty(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "requires_dist": None
            }
        }

        with patch('requests.get', return_value=mock_response):
            dependencies = self.client.get_dependencies(self.random_package, self.random_version)
            self.assertEqual(dependencies, [])

    def test_stream_handling_malformed_json(self):
        garbage_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(garbage_bytes)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = mock_stream

        with patch('requests.get', return_value=mock_response):
            result = self.client.parse_stream_data(mock_stream)
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()