import unittest
import io
import uuid
import random
from skills.package_requirement_parser import PackageRequirementParser, parse_requirement
from skills.pypi_client import PyPIClient

class TestPackageRequirementParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = PackageRequirementParser()
        self.rand_suffix = uuid.uuid4().hex[:6]
        self.pkg_name = f"test-pkg-{self.rand_suffix}"
        self.version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_parse_requirement_direct(self):
        req_str = f"{self.pkg_name} >= {self.version}"
        result = parse_requirement(req_str)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], self.pkg_name)
        self.assertEqual(result["operator"], ">=")
        self.assertEqual(result["version"], self.version)

    def test_parse_stream_integration(self):
        other_pkg = f"dep-{uuid.uuid4().hex[:4]}"
        other_ver = f"2.{random.randint(0, 5)}.0"

        stream_content = f"""
        # Comment line with {uuid.uuid4().hex}
        {self.pkg_name}=={self.version}

        {other_pkg} > {other_ver} ; python_version < "3.10"
        """
        stream = io.StringIO(stream_content.strip())
        results = list(self.parser.parse_stream(stream))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], self.pkg_name)
        self.assertEqual(results[0]["operator"], "==")
        self.assertEqual(results[0]["version"], self.version)

        self.assertEqual(results[1]["name"], other_pkg)
        self.assertEqual(results[1]["operator"], ">")
        self.assertEqual(results[1]["version"], other_ver)

    def test_pypi_client_dependency_parsing_flow(self):
        client = PyPIClient()
        dummy_requires = [
            f"requests >= 2.28.0",
            f"urllib3 < 2.0, >= 1.26.0",
            f"random-lib-{uuid.uuid4().hex[:4]} == 0.1.0"
        ]

        stream_data = io.BytesIO("\n".join(dummy_requires).encode("utf-8"))
        parsed_items = list(self.parser.parse_stream(stream_data))

        self.assertEqual(len(parsed_items), 3)
        self.assertEqual(parsed_items[0]["name"], "requests")
        self.assertEqual(parsed_items[0]["operator"], ">=")
        self.assertEqual(parsed_items[0]["version"], "2.28.0")

        self.assertEqual(parsed_items[2]["operator"], "==")
        self.assertEqual(parsed_items[2]["version"], "0.1.0")

if __name__ == "__main__":
    unittest.main()