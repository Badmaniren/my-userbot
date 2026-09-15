import unittest
import io
import uuid
import random
from skills.requirement_parser import RequirementParser, parse_requirements
from skills.pypi_client import PyPIClient

class TestRequirementParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = RequirementParser()
        self.pypi_client = PyPIClient()
        self.random_suffix = uuid.uuid4().hex[:8]

    def test_parse_pep508_and_stream_integration(self):
        pkg_name = f"requests-{self.random_suffix}"
        target_version = f"2.{random.randint(25, 30)}.{random.randint(0, 9)}"
        req_line = f"{pkg_name} >= {target_version}; python_version < '3.10'"

        parsed_single = self.parser.parse(req_line)
        self.assertEqual(parsed_single["name"], pkg_name)
        self.assertIn(f">={target_version}", parsed_single["specs"])
        self.assertEqual(parsed_single["version"], target_version)
        self.assertIsNotNone(parsed_single["marker"])

        stream_content = f"# Test comment\n\n{req_line}\n"
        stream = io.BytesIO(stream_content.encode("utf-8"))

        parsed_stream = self.parser.parse_stream(stream)
        self.assertIsInstance(parsed_stream, list)
        self.assertTrue(len(parsed_stream) > 0)

        found = False
        for item in parsed_stream:
            if item["name"] == pkg_name:
                found = True
                self.assertEqual(item["version"], target_version)
        self.assertTrue(found, "Parsed stream must contain the requirement line")

    def test_parse_requirements_helper_and_pypi_workflow(self):
        dependency_name = f"click-{uuid.uuid4().hex[:6]}"
        spec_string = f"{dependency_name} == 8.1.3"

        result_list = parse_requirements(spec_string)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 1)

        parsed = result_list[0]
        self.assertEqual(parsed["name"], dependency_name)
        self.assertEqual(parsed["version"], "8.1.3")

        versions = self.pypi_client.get_release_versions("pip")
        self.assertIsInstance(versions, list)

        metadata = self.pypi_client.get_package_metadata("pip", "23.0")
        self.assertIsInstance(metadata, dict)

if __name__ == "__main__":
    unittest.main()