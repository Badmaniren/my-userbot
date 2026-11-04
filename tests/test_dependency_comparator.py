import unittest
from unittest.mock import patch, MagicMock
import io
import os
import random
import uuid
import string
from skills.dependency_comparator import DependencyComparator

class TestDependencyComparator(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.comparator = DependencyComparator(self.repo_path)

    def test_init_sets_repo_path(self):
        expected_path = f"/var/repo/{uuid.uuid4().hex}"
        comparator = DependencyComparator(expected_path)
        self.assertEqual(comparator.repo_path, expected_path)

    def test_normalize_name(self):
        raw_name = f"Pkg_{uuid.uuid4().hex}-Name.v{random.randint(1, 100)}"
        normalized = self.comparator.normalize_name(raw_name)
        self.assertIsInstance(normalized, str)
        self.assertNotIn("_", normalized)
        self.assertNotIn(".", normalized)
        self.assertEqual(normalized, raw_name.lower().replace("_", "-").replace(".", "-"))

    def test_compare_versions_outdated(self):
        dep_name = f"lib-{uuid.uuid4().hex[:6]}"
        local_version = f"1.{random.randint(0, 5)}.{random.randint(0, 9)}"
        latest_version = f"2.{random.randint(0, 5)}.{random.randint(0, 9)}"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "info": {"version": latest_version},
                "releases": {latest_version: [{}]}
            }
            mock_get.return_value = mock_response

            result = self.comparator.compare_version(dep_name, local_version)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("name"), dep_name)
            self.assertEqual(result.get("local_version"), local_version)
            self.assertEqual(result.get("latest_version"), latest_version)
            self.assertTrue(result.get("is_outdated"))

    def test_compare_versions_uptodate(self):
        dep_name = f"pkg-{uuid.uuid4().hex[:6]}"
        version = f"3.{random.randint(0, 9)}.{random.randint(0, 9)}"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "info": {"version": version},
                "releases": {version: [{}]}
            }
            mock_get.return_value = mock_response

            result = self.comparator.compare_version(dep_name, version)
            self.assertFalse(result.get("is_outdated"))
            self.assertEqual(result.get("latest_version"), version)

    def test_parse_dependency_stream(self):
        rand_pkg = f"dependency-{uuid.uuid4().hex[:8]}"
        rand_ver = f"{random.randint(1, 5)}.{random.randint(0, 9)}.0"
        stream_data = f"{rand_pkg}=={rand_ver}\n".encode('utf-8')
        stream = io.BytesIO(stream_data)

        dependencies = self.comparator.parse_dependency_stream(stream)
        self.assertIn(rand_pkg, dependencies)
        self.assertEqual(dependencies[rand_pkg], rand_ver)

    def test_fetch_pypi_data_failure(self):
        dep_name = f"nonexistent-{uuid.uuid4().hex}"
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            data = self.comparator.fetch_pypi_data(dep_name)
            self.assertIsNone(data)

    def test_run_comparison_workflow(self):
        rand_dep = f"module-{uuid.uuid4().hex[:5]}"
        rand_loc_ver = "1.0.0"
        rand_lat_ver = "1.1.0"

        with patch.object(self.comparator, 'scan_local_dependencies', return_value={rand_dep: rand_loc_ver}):
            with patch.object(self.comparator, 'fetch_pypi_data', return_value={"info": {"version": rand_lat_ver}}):
                report = self.comparator.run()
                self.assertIsInstance(report, dict)
                self.assertIn(rand_dep, report.get("outdated", {}))

    def test_process_stream_comparison(self):
        unique_token = uuid.uuid4().hex[:10]
        stream_content = f"sample-lib=={unique_token}\n".encode('ascii')
        stream = io.BytesIO(stream_content)

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"info": {"version": "2.0.0"}}
            mock_get.return_value = mock_resp

            res = self.comparator.process_stream(stream)
            self.assertIsInstance(res, dict)
            self.assertTrue(len(res) > 0)

    def test_evaluate_outdated_status(self):
        major_diff = self.comparator._is_outdated("1.0.0", "2.0.0")
        patch_diff = self.comparator._is_outdated("1.0.0", "1.0.1")
        equal_ver = self.comparator._is_outdated("1.2.3", "1.2.3")

        self.assertTrue(major_diff)
        self.assertTrue(patch_diff)
        self.assertFalse(equal_ver)

    def test_generate_comparison_report(self):
        file_path = f"/tmp/{uuid.uuid4().hex}.json"
        mock_data = {
            uuid.uuid4().hex: {
                "local": f"{random.randint(0,9)}.0.0",
                "latest": f"{random.randint(0,9)}.1.0"
            }
        }
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            res = self.comparator.generate_report(mock_data, file_path)
            self.assertTrue(res)
            mock_file.assert_called_once_with(file_path, 'w', encoding='utf-8')