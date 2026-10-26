import unittest
import io
import uuid
import random
from unittest.mock import patch

from skills.patch_sanitizer import (
    PatchSanitizer,
    PatchSanitizerError,
    sanitize_patch,
)


class TestPatchSanitizerInquisition(unittest.TestCase):
    """Архитектурно-инквизиторские юнит-тесты для модуля PatchSanitizer."""

    def setUp(self):
        self.sanitizer = PatchSanitizer()
        self.rand_prefix = uuid.uuid4().hex[:8]

    def test_sanitize_success(self):
        line_one = f"{self.rand_prefix}_alpha   "
        line_two = f"{self.rand_prefix}_beta\r\n"
        raw_content = f"{line_one}\n{line_two}"
        
        stream = io.StringIO(raw_content)
        result = self.sanitizer.sanitize(stream)
        
        expected_line_one = f"{self.rand_prefix}_alpha"
        expected_line_two = f"{self.rand_prefix}_beta"
        expected_output = f"{expected_line_one}\n{expected_line_two}"
        
        self.assertEqual(result, expected_output)

    def test_sanitize_empty_stream_error(self):
        stream = io.StringIO("")
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_sanitize_null_bytes_error(self):
        raw_content = f"{uuid.uuid4().hex}\x00{uuid.uuid4().hex}"
        stream = io.StringIO(raw_content)
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_normalize_endings(self):
        part_one = uuid.uuid4().hex
        part_two = uuid.uuid4().hex
        part_three = uuid.uuid4().hex
        raw_content = f"{part_one}\r\n{part_two}\r{part_three}\n"
        
        stream = io.StringIO(raw_content)
        result = self.sanitizer.normalize_endings(stream)
        
        self.assertNotIn("\r\n", result)
        self.assertNotIn("\r", result)
        self.assertIn(part_one, result)
        self.assertIn(part_two, result)
        self.assertIn(part_three, result)

    def test_strip_whitespace(self):
        token = uuid.uuid4().hex
        raw_content = f"  {token}   \r\n"
        
        stream = io.StringIO(raw_content)
        result = self.sanitizer.strip_whitespace(stream)
        
        self.assertTrue(result.endswith("\n"))
        self.assertIn(token, result)

    def test_remove_binary_diffs(self):
        token_a = uuid.uuid4().hex
        token_b = uuid.uuid4().hex
        raw_content = (
            f"index {token_a}..{token_b}\n"
            f"Binary files a/{token_a} and b/{token_b} differ\n"
            f"--- a/{token_a}\n"
            f"+++ b/{token_b}\n"
        )
        
        stream = io.StringIO(raw_content)
        result = self.sanitizer.remove_binary_diffs(stream)
        
        self.assertNotIn("Binary files", result)
        self.assertNotIn("differ", result)
        self.assertIn(token_a, result)
        self.assertIn(token_b, result)

    def test_wrapper_sanitize_patch(self):
        dynamic_tag = uuid.uuid4().hex
        raw_payload = f"   {dynamic_tag}   \r\n"
        
        output = sanitize_patch(raw_payload)
        self.assertEqual(output.strip(), dynamic_tag)


if __name__ == "__main__":
    unittest.main()