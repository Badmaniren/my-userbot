import unittest
import io
import uuid
import random
from skills.requirement_parser import RequirementParser, parse_requirement

class TestRequirementParserIntegration(unittest.TestCase):

    def setUp(self):
        self.parser = RequirementParser()
        self.random_suffix = uuid.uuid4().hex[:8]

    def test_parse_valid_requirement(self):
        pkg_name = f"secure-package-{self.random_suffix}"
        minor_version = random.randint(1, 9)
        patch_version = random.randint(0, 9)
        req_line = f"{pkg_name} >= 1.{minor_version}.{patch_version}"

        result = self.parser.parse(req_line)

        self.assertEqual(result["name"], pkg_name)
        self.assertEqual(result["operator"], ">=")
        self.assertEqual(result["version"], f"1.{minor_version}.{patch_version}")

        audit_prep = self.parser.prepare_for_audit(result)
        self.assertEqual(audit_prep["package"], pkg_name)
        self.assertEqual(audit_prep["constraint"], f">=1.{minor_version}.{patch_version}")

    def test_parse_stream_and_integration(self):
        pkg1 = f"auth-lib-{self.random_suffix}"
        pkg2 = f"crypto-core-{self.random_suffix}"

        stream_content = f"""
        # Security audit requirements stream
        {pkg1} == 2.{random.randint(0, 5)}.0
        {pkg2} > 3.0.0; python_version < "3.11"
        """.strip().encode("utf-8")

        stream = io.BytesIO(stream_content)
        parsed_list = self.parser.parse_stream(stream)

        self.assertGreaterEqual(len(parsed_list), 2)

        names = [item["name"] for item in parsed_list]
        self.assertIn(pkg1, names)
        self.assertIn(pkg2, names)

        for item in parsed_list:
            audit_data = self.parser.prepare_for_audit(item)
            self.assertIn("package", audit_data)
            self.assertIn("constraint", audit_data)
            self.assertTrue(len(audit_data["package"]) > 0)

    def test_parse_invalid_requirement_raises_value_error(self):
        invalid_line = f"invalid__package_name_!@#$ {self.random_suffix}"

        with self.assertRaises(ValueError):
            self.parser.parse(invalid_line)

        with self.assertRaises(ValueError):
            parse_requirement(invalid_line)

    def test_empty_or_comment_stream_lines(self):
        comment_line = f"# comment {self.random_suffix}"
        stream = io.BytesIO(f"\n   \n{comment_line}\n".encode("utf-8"))

        parsed_list = self.parser.parse_stream(stream)
        self.assertEqual(len(parsed_list), 0)

        with self.assertRaises(ValueError):
            self.parser.parse(comment_line)

if __name__ == "__main__":
    unittest.main()