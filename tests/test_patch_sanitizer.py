import io
import random
import unittest
import uuid
from unittest.mock import patch

from skills.patch_sanitizer import (
    PatchSanitizer,
    PatchSanitizerError,
    sanitize_patch,
)


class TestPatchSanitizer(unittest.TestCase):

    def setUp(self):
        self.sanitizer = PatchSanitizer()
        self.random_prefix = uuid.uuid4().hex
        self.random_suffix = uuid.uuid4().hex

    def test_sanitize_empty_stream_raises_error(self):
        empty_stream = io.StringIO("")
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(empty_stream)

    def test_sanitize_null_bytes_raises_error(self):
        corrupted_content = f"diff --git a/{self.random_prefix} b/{self.random_suffix}\n\x00corrupted"
        stream = io.StringIO(corrupted_content)
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_sanitize_success_normalization_and_strip(self):
        line_one = f"index {self.random_prefix}..{uuid.uuid4().hex} 100644   "
        line_two = f"+print('{self.random_suffix}')\r\n"
        line_three = f"--- a/{self.random_prefix}.py\r"
        
        raw_content = f"{line_one}\n{line_two}{line_three}"
        stream = io.StringIO(raw_content)

        result = self.sanitizer.sanitize(stream)
        
        self.assertNotIn("\r", result)
        self.assertNotIn("   \n", result)
        self.assertIn(self.random_prefix, result)
        self.assertIn(self.random_suffix, result)

    def test_normalize_endings_crlf_and_cr(self):
        unique_token = uuid.uuid4().hex
        content = f"line1_{unique_token}\r\nline2_{unique_token}\rmiddle\nend_{unique_token}"
        stream = io.StringIO(content)
        
        normalized = self.sanitizer.normalize_endings(stream)
        
        self.assertNotIn("\r\n", normalized)
        self.assertNotIn("\r", normalized.replace("\n", ""))
        self.assertEqual(normalized.count("\n"), 3)
        self.assertIn(unique_token, normalized)

    def test_strip_whitespace_preserves_trailing_newline_correctly(self):
        unique_val = uuid.uuid4().hex
        content_with_newline = f"  {unique_val}   \r\n"
        stream_one = io.StringIO(content_with_newline)
        
        res_one = self.sanitizer.strip_whitespace(stream_one)
        self.assertTrue(res_one.endswith("\n"))
        self.assertIn(unique_val, res_one)

        content_without_newline = f"  {uuid.uuid4().hex}   "
        stream_two = io.StringIO(content_without_newline)
        
        res_two = self.sanitizer.strip_whitespace(stream_two)
        self.assertFalse(res_two.endswith("\n"))

    def test_remove_binary_diffs_filters_correctly(self):
        target_token = uuid.uuid4().hex
        noise_token = uuid.uuid4().hex
        
        content = (
            f"index {target_token}..{uuid.uuid4().hex}\n"
            f"Binary files a/{noise_token}.png and b/{noise_token}.png differ\n"
            f"--- a/{target_token}.py\n"
            f"+++ b/{target_token}.py\n"
        )
        stream = io.StringIO(content)

        cleaned = self.sanitizer.remove_binary_diffs(stream)
        
        self.assertNotIn("Binary files", cleaned)
        self.assertNotIn("differ", cleaned)
        self.assertIn(target_token, cleaned)

    def test_sanitize_patch_wrapper_function(self):
        rand_str = uuid.uuid4().hex
        raw_patch = f"diff --git a/{rand_str} b/{rand_str}\n+content_{rand_str}   \r\n"
        
        output = sanitize_patch(raw_patch)
        
        self.assertIn(rand_str, output)
        self.assertNotIn("\r", output)
        self.assertFalse(output.endswith("   "))


if __name__ == "__main__":
    unittest.main()