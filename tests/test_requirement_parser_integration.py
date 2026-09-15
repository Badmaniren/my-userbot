import unittest
import io
import uuid
import random
from skills.requirement_parser import RequirementParser, ParsedRequirement, parse_requirements_line
from skills.pypi_client import PyPIClient

class TestRequirementParserIntegration(unittest.TestCase):
    def setUp(self):
        self.pypi_client = PyPIClient()
        self.parser = RequirementParser(pypi_client=self.pypi_client)
        self.random_tag = uuid.uuid4().hex[:8]

    def test_parse_requirement_and_stream_integration(self):
        pkg_name = f"reqtest-{self.random_tag}"
        version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"
        req_string = f"{pkg_name}=={version} ; python_version < '3.10'"

        parsed = self.parser.parse_requirement(req_string)
        self.assertIsInstance(parsed, ParsedRequirement)
        self.assertEqual(parsed.name, pkg_name)
        self.assertEqual(parsed.get("version"), version)
        self.assertIn("python_version", parsed.get("environment_markers"))

        stream_content = f"# Comment line\n{req_string}\nrequests>=2.28.0"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        results = self.parser.parse_stream(stream)
        self.assertGreaterEqual(len(results), 2)

        names = [r.name for r in results]
        self.assertIn(pkg_name, names)
        self.assertIn("requests", names)

    def test_resolve_with_pypi_integration(self):
        test_packages = ["requests", "urllib3", "pip"]
        chosen_package = random.choice(test_packages)

        versions = self.pypi_client.get_release_versions(chosen_package)
        if versions:
            chosen_version = versions[-1]
            resolved_deps = self.parser.resolve_with_pypi(chosen_package, chosen_version)
            self.assertIsInstance(resolved_deps, list)
            for dep in resolved_deps:
                self.assertIsInstance(dep, ParsedRequirement)
                self.assertTrue(len(dep.name) > 0)

    def test_parse_requirements_line_helper(self):
        rand_ver = f"{random.randint(1, 5)}.{random.randint(0, 9)}"
        line = f"numpy == {rand_ver} # important dependency"
        res_dict = parse_requirements_line(line)

        self.assertEqual(res_dict["name"], "numpy")
        self.assertEqual(res_dict["version"], rand_ver)
        self.assertIsInstance(res_dict["extras"], list)
        self.assertIsInstance(res_dict["environment_markers"], str)

if __name__ == "__main__":
    unittest.main()