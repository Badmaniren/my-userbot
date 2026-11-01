import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.patch_regression_suite import PatchRegressionSuite, PatchRegressionSuiteError

class TestPatchRegressionSuite(unittest.TestCase):

    def setUp(self):
        self.random_suite_id = uuid.uuid4().hex
        self.suite = PatchRegressionSuite(suite_id=self.random_suite_id)
        self.random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32))

    def test_init_default_suite_id(self):
        default_suite = PatchRegressionSuite()
        self.assertIsNotNone(default_suite.suite_id)
        self.assertIsInstance(default_suite.suite_id, str)
        self.assertFalse(default_suite.executed)

    def test_init_custom_suite_id(self):
        custom_suite = PatchRegressionSuite(suite_id=self.random_suite_id)
        self.assertEqual(custom_suite.suite_id, self.random_suite_id)
        self.assertFalse(custom_suite.executed)

    def test_run_suite_success(self):
        result = self.suite.run_suite(self.random_payload)
        self.assertTrue(self.suite.executed)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("suite_id"), self.random_suite_id)
        self.assertEqual(result.get("status"), "passed")
        self.assertIn("signature", result)
        self.assertEqual(result.get("payload_len"), len(self.random_payload))

    def test_run_suite_empty_payload_raises_error(self):
        with self.assertRaises(PatchRegressionSuiteError):
            self.suite.run_suite("")
        self.assertFalse(self.suite.executed)

    def test_run_suite_none_payload_raises_error(self):
        with self.assertRaises(PatchRegressionSuiteError):
            self.suite.run_suite(None)
        self.assertFalse(self.suite.executed)

    def test_run_suite_signature_uniqueness(self):
        payload_one = uuid.uuid4().hex
        payload_two = uuid.uuid4().hex

        res_one = self.suite.run_suite(payload_one)
        sig_one = res_one.get("signature")

        suite_two = PatchRegressionSuite()
        res_two = suite_two.run_suite(payload_two)
        sig_two = res_two.get("signature")

        self.assertNotEqual(sig_one, sig_two)