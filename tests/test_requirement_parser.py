import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.requirement_parser import parse_requirement

class TestRequirementParser(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.pkg_name = f"pkg-{self.rand_suffix}"
        self.version_num = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.operators = random.choice(['==', '>=', '<=', '>', '<', '~=', '!='])

    def test_parse_simple_package_name(self):
        raw_req = self.pkg_name
        name, constraints = parse_requirement(raw_req)
        self.assertEqual(name, self.pkg_name)
        self.assertEqual(constraints, [])

    def test_parse_package_with_version_constraint(self):
        raw_req = f"{self.pkg_name} ({self.operators}{self.version_num})"
        name, constraints = parse_requirement(raw_req)
        self.assertEqual(name, self.pkg_name)
        self.assertIn((self.operators, self.version_num), constraints)

    def test_parse_package_with_multiple_constraints(self):
        sec_version = f"9.{random.randint(0, 9)}.0"
        raw_req = f"{self.pkg_name} (>={self.version_num}, <{sec_version})"
        name, constraints = parse_requirement(raw_req)
        self.assertEqual(name, self.pkg_name)
        self.assertIn(('>=', self.version_num), constraints)
        self.assertIn(('<', sec_version), constraints)

    def test_parse_with_extras(self):
        extra_name = f"extra_{uuid.uuid4().hex[:4]}"
        raw_req = f"{self.pkg_name}[{extra_name}] ({self.operators}{self.version_num})"
        name, constraints = parse_requirement(raw_req)
        self.assertEqual(name, self.pkg_name)
        self.assertIn((self.operators, self.version_num), constraints)

    def test_parse_stream_data_mock(self):
        stream_content = f"{self.pkg_name} >={self.version_num}\n".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)
        
        parsed_list = []
        for line in mock_stream:
            decoded = line.decode('utf-8').strip()
            if decoded:
                name, constraints = parse_requirement(decoded)
                parsed_list.append((name, constraints))
                
        self.assertTrue(len(parsed_list) > 0)
        self.assertEqual(parsed_list[0][0], self.pkg_name)
        self.assertIn(('>=', self.version_num), parsed_list[0][1])

    def test_chaos_random_requirement_string(self):
        random_chars = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_req_str = f"lib-{random_chars} (=={random.randint(1,5)}.0.0)"
        name, constraints = parse_requirement(rand_req_str)
        self.assertEqual(name, f"lib-{random_chars}")
        self.assertEqual(len(constraints), 1)
        self.assertEqual(constraints[0][0], '==')

if __name__ == '__main__':
    unittest.main()