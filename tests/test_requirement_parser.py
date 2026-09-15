import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
from skills.requirement_parser import (
    ParsedRequirement,
    RequirementParser,
    parse_requirements_line
)

class TestRequirementParser(unittest.TestCase):
    def setUp(self):
        self.rand_pkg = f"pkg-{uuid.uuid4().hex[:8]}"
        self.rand_ver = f"{random.randint(0, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.rand_extra = f"extra-{uuid.uuid4().hex[:6]}"
        self.rand_marker_expr = f"python_version < '{random.randint(3, 4)}.{random.randint(0, 9)}'"

    def test_parse_requirement_valid(self):
        req_str = f"{self.rand_pkg}=={self.rand_ver}[{self.rand_extra}]; {self.rand_marker_expr}"
        parser = RequirementParser()
        result = parser.parse_requirement(req_str)

        self.assertIsInstance(result, ParsedRequirement)
        self.assertEqual(result.name, self.rand_pkg)
        self.assertIn(self.rand_ver, result.version_specifier)
        self.assertIn(self.rand_extra, result.extras)
        self.assertTrue("python_version" in result.environment_markers)

        self.assertEqual(result.get("name"), self.rand_pkg)
        self.assertEqual(result.get("version"), self.rand_ver)
        self.assertIn(self.rand_extra, result.get("extras"))
        self.assertTrue("python_version" in result.get("environment_markers"))
        self.assertEqual(result.get(uuid.uuid4().hex), None)

    def test_parse_requirement_invalid(self):
        bad_req = f"==={uuid.uuid4().hex}"
        parser = RequirementParser()
        with self.assertRaises(ValueError):
            parser.parse_requirement(bad_req)

    def test_parse_stream(self):
        line1 = f"{self.rand_pkg}=={self.rand_ver}"
        rand_pkg2 = f"lib-{uuid.uuid4().hex[:6]}"
        stream_content = f"# Comment\n\n   {line1}   \n{rand_pkg2} >= 1.0.0 # inline comment\n"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        parser = RequirementParser()
        results = parser.parse_stream(stream)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, self.rand_pkg)
        self.assertEqual(results[1].name, rand_pkg2)

    def test_resolve_with_pypi(self):
        dep_str = f"dep-{uuid.uuid4().hex[:6]} >= 2.0"
        with patch('skills.requirement_parser.PyPIClient') as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.get_dependencies.return_value = [dep_str]

            parser = RequirementParser(pypi_client=mock_instance)
            resolved = parser.resolve_with_pypi(self.rand_pkg, self.rand_ver)

            mock_instance.get_dependencies.assert_called_once_with(self.rand_pkg, self.rand_ver)
            self.assertEqual(len(resolved), 1)
            self.assertEqual(resolved[0].name, dep_str.split()[0])

    def test_parse_requirements_line_function(self):
        req_line = f"{self.rand_pkg}>=1.2.3 # some comment"
        res_dict = parse_requirements_line(req_line)

        self.assertEqual(res_dict["name"], self.rand_pkg)
        self.assertEqual(res_dict["version"], "1.2.3")
        self.assertIsInstance(res_dict["extras"], list)
        self.assertIsInstance(res_dict["environment_markers"], str)

    def test_fallback_without_packaging(self):
        req_str = f"{self.rand_pkg}=={self.rand_ver}[{self.rand_extra}]; python_version < '3.8'"
        parser = RequirementParser()
        with patch('skills.requirement_parser.HAS_PACKAGING', False):
            result = parser.parse_requirement(req_str)
            self.assertEqual(result.name, self.rand_pkg)
            self.assertEqual(result.get("version"), self.rand_ver)
            self.assertIn(self.rand_extra, result.extras)
            self.assertIn("python_version < '3.8'", result.environment_markers)

if __name__ == '__main__':
    unittest.main()