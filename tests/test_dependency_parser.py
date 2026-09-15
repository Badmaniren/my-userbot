import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import skills.dependency_parser as dp
from skills.dependency_parser import (
    parse_dependency,
    parse_stream_data,
    PyPIClient,
    Dependency,
    DependencyParserError,
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator,
    PipelineResult
)

class TestDependencyParser(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:6]
        self.pkg_name = f"pkg-{self.rand_suffix}"
        self.ver_num = f"{random.randint(1,9)}.{random.randint(0,9)}.{random.randint(0,9)}"
        self.extra_name = f"extra-{uuid.uuid4().hex[:4]}"
        self.marker_var = f"python_version < '{random.randint(3,4)}.{random.randint(0,9)}'"

    def test_parse_dependency_valid_simple(self):
        req_str = f"{self.pkg_name}=={self.ver_num}"
        dep = parse_dependency(req_str)
        self.assertEqual(dep.name.lower(), self.pkg_name.lower())
        self.assertIn(self.ver_num, dep.version_constraint)

    def test_parse_dependency_with_marker_and_extras(self):
        req_str = f"{self.pkg_name}[{self.extra_name}]>={self.ver_num}; {self.marker_var}"
        dep = parse_dependency(req_str)
        self.assertEqual(dep.name.lower(), self.pkg_name.lower())
        self.assertIn(self.extra_name, dep.extras)
        self.assertIsNotNone(dep.marker)
        self.assertIn(self.ver_num, dep.version_constraint)

    def test_parse_dependency_empty_raises(self):
        invalid_inputs = ["", "   ", None, 123]
        for inv in invalid_inputs:
            with self.subTest(inv=inv):
                if inv is None or isinstance(inv, int):
                    with self.assertRaises(DependencyParserError):
                        parse_dependency(inv) # type: ignore
                else:
                    with self.assertRaises(DependencyParserError):
                        parse_dependency(inv)

    def test_parse_dependency_syntax_error_raises(self):
        bad_str = f"===invalid==package_name=={uuid.uuid4().hex}"
        with self.assertRaises(DependencyParserError):
            parse_dependency(bad_str)

    def test_parse_dependency_fallback_when_no_packaging(self):
        req_str = f"{self.pkg_name}[{self.extra_name}] (>= {self.ver_num}); {self.marker_var}"
        with patch("skills.dependency_parser.HAS_PACKAGING", False):
            dep = parse_dependency(req_str)
            self.assertEqual(dep.name.lower(), self.pkg_name.lower())
            self.assertIn(self.extra_name, dep.extras)
            self.assertIsNotNone(dep.marker)
            self.assertIn(self.ver_num, dep.version_constraint)

    def test_parse_dependency_fallback_invalid_syntax(self):
        bad_str = f"===invalid==package_name=={uuid.uuid4().hex}"
        with patch("skills.dependency_parser.HAS_PACKAGING", False):
            with self.assertRaises(DependencyParserError):
                parse_dependency(bad_str)

    def test_parse_stream_data_bytes_io(self):
        dep_line = f"{self.pkg_name}=={self.ver_num}\n"
        stream = io.BytesIO(dep_line.encode('utf-8'))
        results = parse_stream_data(stream)
        self.assertTrue(len(results) > 0)
        found = any(r["name"].lower() == self.pkg_name.lower() for r in results)
        self.assertTrue(found)

    def test_parse_stream_data_dict(self):
        stream_dict = {
            "requires_dist": [
                f"{self.pkg_name}>={self.ver_num}"
            ]
        }
        results = parse_stream_data(stream_dict)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"].lower(), self.pkg_name.lower())

    def test_parse_stream_data_string(self):
        single_str = f"{self.pkg_name}=={self.ver_num}"
        results = parse_stream_data(single_str)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["name"].lower(), self.pkg_name.lower())


class TestPyPIClientAndPipeline(unittest.TestCase):

    def setUp(self):
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.exc_msg = f"err_{uuid.uuid4().hex[:8]}"
        self.tb_str = f"traceback_{uuid.uuid4().hex[:8]}"
        self.inc_id = str(uuid.uuid4())

    def test_pypi_client_parse_stream_data_dict(self):
        client = PyPIClient()
        pkg = f"lib-{uuid.uuid4().hex[:6]}"
        ver = f"{random.randint(1,5)}.0"
        data = {"requires_dist": [f"{pkg}=={ver}"]}
        parsed = client.parse_stream_data(data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["name"].lower(), pkg.lower())

    def test_pypi_client_parse_stream_data_invalid(self):
        client = PyPIClient()
        res = client.parse_stream_data(io.BytesIO(b"garbage"))
        self.assertEqual(res, [])

    def test_auto_patch_pipeline_run(self):
        pipeline = AutoPatchPipeline()
        exc = RuntimeError(self.exc_msg)
        result = pipeline.run_pipeline(self.module_name, exc, self.tb_str, {"rand": uuid.uuid4().hex})
        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.incident_id)

        history = pipeline.recovery_hub.get_incident_history(self.module_name)
        self.assertIn(result.incident_id, history)

        logs = pipeline.recovery_hub.get_incident_logs(result.incident_id)
        self.assertEqual(logs["module"], self.module_name)
        self.assertEqual(logs["exception"], self.exc_msg)

    def test_auto_patch_pipeline_force_recover(self):
        pipeline = AutoPatchPipeline()
        exc = ValueError(self.exc_msg)
        result = pipeline.force_analyze_and_recover(self.module_name, exc, {"uuid": uuid.uuid4().hex})
        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.incident_id)

    def test_patch_validator(self):
        validator = PatchValidator()
        stream_data = {"package": f"pkg_{uuid.uuid4().hex[:4]}"}
        ver_res = validator.verify_stream(stream_data)
        self.assertEqual(ver_res["status"], "verified")
        self.assertEqual(ver_res["package"], stream_data["package"])

        valid_patch = {"code": f"print('{uuid.uuid4().hex}')"}
        self.assertTrue(validator.validate(valid_patch))
        self.assertFalse(validator.validate({"invalid": "dict"}))
