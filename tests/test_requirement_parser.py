import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.requirement_parser import RequirementParser, parse_requirement

class TestRequirementParser(unittest.TestCase):
    def setUp(self):
        self.parser = RequirementParser()
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.pkg_name = f"pkg-{self.rand_suffix}"
        self.version_num = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_parse_valid_requirement(self):
        op = random.choice([">=", "==", "<=", "~=", ">", "<"])
        req_line = f"{self.pkg_name} {op} {self.version_num}"

        mock_req = MagicMock()
        mock_req.name = self.pkg_name
        mock_req.specifier = f"{op}{self.version_num}"
        mock_req.extras = None
        mock_req.marker = None

        with patch("skills.requirement_parser.Requirement", return_value=mock_req):
            res = self.parser.parse(req_line)
            self.assertEqual(res["name"], self.pkg_name)
            self.assertEqual(res["operator"], op)
            self.assertEqual(res["version"], self.version_num)

    def test_parse_empty_or_comment(self):
        empty_line = "   "
        comment_line = f"# {uuid.uuid4().hex}"

        with self.assertRaises(ValueError):
            self.parser.parse(empty_line)

        with self.assertRaises(ValueError):
            self.parser.parse(comment_line)

    def test_parse_invalid_requirement_raises(self):
        bad_line = f"!invalid@@{uuid.uuid4().hex}"
        with patch("skills.requirement_parser.Requirement", side_effect=Exception("Invalid")):
            with self.assertRaises(ValueError):
                self.parser.parse(bad_line)

    def test_parse_stream(self):
        line1 = f"package-alpha-{self.rand_suffix} >= 1.0.0"
        line2 = f"# comment {uuid.uuid4().hex}"
        line3 = f"package-beta-{self.rand_suffix} == 2.0.0"

        stream_content = f"{line1}\n{line2}\n{line3}\n".encode("utf-8")
        stream = io.BytesIO(stream_content)

        mock_req1 = MagicMock()
        mock_req1.name = f"package-alpha-{self.rand_suffix}"
        mock_req1.specifier = ">=1.0.0"
        mock_req1.extras = None
        mock_req1.marker = None

        mock_req3 = MagicMock()
        mock_req3.name = f"package-beta-{self.rand_suffix}"
        mock_req3.specifier = "==2.0.0"
        mock_req3.extras = None
        mock_req3.marker = None

        def side_effect(arg):
            if "alpha" in arg:
                return mock_req1
            elif "beta" in arg:
                return mock_req3
            raise Exception("Invalid")

        with patch("skills.requirement_parser.Requirement", side_effect=side_effect):
            results = self.parser.parse_stream(stream)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["name"], f"package-alpha-{self.rand_suffix}")
            self.assertEqual(results[1]["name"], f"package-beta-{self.rand_suffix}")

    def test_prepare_for_audit(self):
        op = random.choice([">=", "==", "~="])
        parsed = {
            "name": self.pkg_name,
            "operator": op,
            "version": self.version_num
        }
        audit_data = self.parser.prepare_for_audit(parsed)
        self.assertEqual(audit_data["package"], self.pkg_name)
        self.assertEqual(audit_data["constraint"], f"{op}{self.version_num}")

    def test_module_level_parse_requirement(self):
        req_line = f"{self.pkg_name}=={self.version_num}"
        mock_req = MagicMock()
        mock_req.name = self.pkg_name
        mock_req.specifier = f"=={self.version_num}"
        mock_req.extras = None
        mock_req.marker = None

        with patch("skills.requirement_parser.Requirement", return_value=mock_req):
            res = parse_requirement(req_line)
            self.assertEqual(res["name"], self.pkg_name)

if __name__ == "__main__":
    unittest.main()