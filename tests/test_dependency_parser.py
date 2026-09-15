import unittest
from unittest.mock import patch
import io
import sys
import uuid
import random
import importlib
import skills.dependency_parser
from skills.dependency_parser import DependencyParser, parse_dependency, parse_dependency_string

class TestDependencyParser(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.rand_str = uuid.uuid4().hex[:8]
        self.pkg_name = f"pkg-{self.rand_str}"
        self.version_num = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.op = random.choice(['==', '>=', '<=', '>', '<', '!=', '~='])

    def test_parse_valid_simple_requirement(self):
        req_str = f"{self.pkg_name} {self.op} {self.version_num}"
        result = self.parser.parse(req_str)
        self.assertEqual(result['name'], self.pkg_name)
        self.assertEqual(result['operator'], self.op)
        self.assertEqual(result['version'], self.version_num)
        self.assertEqual(result['extras'], [])
        self.assertIsNone(result['marker'])

    def test_parse_requirement_with_extras_and_marker(self):
        extra_name = f"extra-{uuid.uuid4().hex[:4]}"
        marker_var = f"python_version {random.choice(['>', '<', '=='])} '3.{random.randint(7, 12)}'"
        req_str = f"{self.pkg_name}[{extra_name}] {self.op} {self.version_num} ; {marker_var}"

        result = self.parser.parse(req_str)
        self.assertEqual(result['name'], self.pkg_name)
        self.assertEqual(result['operator'], self.op)
        self.assertEqual(result['version'], self.version_num)
        self.assertIn(extra_name, result['extras'])
        self.assertIsNotNone(result['marker'])

    def test_parse_invalid_requirement_raises_value_error(self):
        bad_req = f"=={uuid.uuid4().hex}"
        with self.assertRaises(ValueError):
            self.parser.parse(bad_req)

    def test_parse_stream_valid_and_invalid_lines(self):
        valid_req = f"package-{uuid.uuid4().hex[:6]} >= {self.version_num}"
        comment_line = f"# {uuid.uuid4().hex}"
        empty_line = "   "
        stream_content = f"{comment_line}\n{valid_req} # inline comment\n{empty_line}\n"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        results = self.parser.parse_stream(stream)
        self.assertEqual(len(results), 1)
        self.assertIn('name', results[0])

    def test_module_level_helpers(self):
        req_str = f"helper-{uuid.uuid4().hex[:6]} == {self.version_num}"
        res1 = parse_dependency(req_str)
        self.assertIsInstance(res1, dict)

        bad_res = parse_dependency_string(f"??? invalid {uuid.uuid4().hex}")
        self.assertIsNone(bad_res)

        good_res = parse_dependency_string(req_str)
        self.assertIsNotNone(good_res)

    def test_packaging_requirement_mock_fallback(self):
        with patch('skills.dependency_parser.Requirement') as mock_req_cls:
            mock_instance = mock_req_cls.return_value
            mock_instance.name = self.pkg_name
            mock_instance.specifier = []
            mock_instance.extras = None
            mock_instance.marker = None

            res = self.parser.parse(self.pkg_name)
            self.assertEqual(res['name'], self.pkg_name)
            self.assertIsNone(res['operator'])
            self.assertIsNone(res['version'])
            self.assertEqual(res['extras'], [])
            self.assertIsNone(res['marker'])

    def test_fallback_when_packaging_not_installed(self):
        # Simulate packaging missing
        with patch.dict(sys.modules, {'packaging': None, 'packaging.requirements': None}):
            # Re-import skills.dependency_parser under simulated missing packaging module
            mod = importlib.import_module('skills.dependency_parser')
            importlib.reload(mod)
            try:
                parser = mod.DependencyParser()
                req_str = f"{self.pkg_name}[extra1] {self.op} {self.version_num} ; python_version > '3.8'"
                res = parser.parse(req_str)
                self.assertEqual(res['name'], self.pkg_name)
                self.assertEqual(res['operator'], self.op)
                self.assertEqual(res['version'], self.version_num)
                self.assertIn('extra1', res['extras'])
                self.assertIsNotNone(res['marker'])

                bad_res = mod.parse_dependency_string("===invalid===")
                self.assertIsNone(bad_res)
            finally:
                # Reload module to restore original state
                importlib.reload(mod)
