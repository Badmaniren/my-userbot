import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.package_requirement_parser import PackageRequirementParser

class TestPackageRequirementParser(unittest.TestCase):
    def setUp(self):
        self.parser = PackageRequirementParser()
        self.random_pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_dep_name = f"dep-{uuid.uuid4().hex[:8]}"
        self.random_marker = f"python_version < '{random.choice([3.7, 3.8, 3.9])}'"
        self.random_req_string = f"{self.random_dep_name} >= {self.random_version}; {self.random_marker}"

    def test_parse_requirements_success(self):
        requires_dist = [
            self.random_req_string,
            f"another-dep[security] == 1.2.3 ; extra == 'test'",
            "simple-package"
        ]

        metadata = {
            "info": {
                "name": self.random_pkg_name,
                "version": self.random_version,
                "requires_dist": requires_dist
            }
        }

        parsed = self.parser.parse_requirements(metadata)

        self.assertIsInstance(parsed, list)
        self.assertTrue(any(d.get("name") == self.random_dep_name for d in parsed))

        target_dep = next((d for d in parsed if d.get("name") == self.random_dep_name), None)
        self.assertIsNotNone(target_dep)
        self.assertEqual(target_dep.get("version_constraint"), f">= {self.random_version}")
        self.assertEqual(target_dep.get("marker"), self.random_marker)

    def test_parse_requirements_empty_and_malformed(self):
        malformed_metadata = {
            "info": {
                "name": f"bad-{uuid.uuid4().hex[:6]}",
                "version": "0.0.1",
                "requires_dist": [None, "", "   ", "invalid requirement string with  weird chars"]
            }
        }

        parsed = self.parser.parse_requirements(malformed_metadata)
        self.assertIsInstance(parsed, list)

    def test_extract_chain_dependencies_recursive(self):
        sub_dep_name = f"sub-{uuid.uuid4().hex[:6]}"

        mock_response_data = {
            "info": {
                "name": self.random_pkg_name,
                "version": self.random_version,
                "requires_dist": [f"{self.random_dep_name} >= 1.0.0"]
            }
        }

        mock_sub_response_data = {
            "info": {
                "name": self.random_dep_name,
                "version": "1.0.0",
                "requires_dist": [f"{sub_dep_name} == 2.0.0"]
            }
        }

        def side_effect(pkg, ver=None):
            if pkg == self.random_pkg_name:
                return mock_response_data
            elif pkg == self.random_dep_name:
                return mock_sub_response_data
            return {"info": {"requires_dist": []}}

        with patch.object(self.parser, 'get_package_metadata', side_effect=side_effect) as mock_get_meta:
            chain = self.parser.extract_dependency_chain(self.random_pkg_name, self.random_version, depth=2)
            self.assertIn(self.random_dep_name, chain)
            self.assertIn(sub_dep_name, chain)
            self.assertGreaterEqual(mock_get_meta.call_count, 2)

    def test_parse_stream_metadata_bytes(self):
        random_json_content = f'{{"info":{{"name":"{self.random_pkg_name}","version":"{self.random_version}","requires_dist":["{self.random_req_string}"]}}}}'
        stream_data = io.BytesIO(random_json_content.encode('utf-8'))

        result = self.parser.parse_stream_data(stream_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("info", {}).get("name"), self.random_pkg_name)
        self.assertEqual(result.get("info", {}).get("version"), self.random_version)

    def test_parse_stream_data_invalid(self):
        garbage_bytes = ''.join(random.choices(string.ascii_letters + string.punctuation, k=64)).encode('latin1')
        stream_data = io.BytesIO(garbage_bytes)

        result = self.parser.parse_stream_data(stream_data)
        self.assertIsNone(result)