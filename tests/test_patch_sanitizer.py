import unittest
from unittest.mock import patch
import random
import uuid
import string
import io

from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError


class TestPatchSanitizer(unittest.TestCase):

    def setUp(self):
        self.sanitizer = PatchSanitizer()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.random_suffix = uuid.uuid4().hex[:8]

    def test_sanitize_valid_patch_returns_cleaned(self):
        dynamic_content = f"diff --git a/{self.random_prefix}.py b/{self.random_prefix}.py\n" \
                          f"--- a/{self.random_prefix}.py\n" \
                          f"+++ b/{self.random_prefix}.py\n" \
                          f"@@ -1,3 +1,3 @@\n" \
                          f"-print('{self.random_suffix}')\n" \
                          f"+print('{self.random_suffix}_updated')"

        stream = io.StringIO(dynamic_content)
        result = self.sanitizer.sanitize(stream)

        self.assertIn(self.random_prefix, result)
        self.assertIn(self.random_suffix, result)
        self.assertNotIn("\r\n", result)

    def test_sanitize_with_null_bytes_raises_error(self):
        malicious_content = f"diff --git a/file.py b/file.py\x00\n+{self.random_prefix}"
        stream = io.StringIO(malicious_content)

        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_normalize_line_endings(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        raw_data = f"{line1}\r\n{line2}\r\n"
        stream = io.StringIO(raw_data)

        normalized = self.sanitizer.normalize_endings(stream)
        self.assertNotIn("\r", normalized)
        self.assertIn(line1, normalized)
        self.assertIn(line2, normalized)

    def test_strip_trailing_whitespace(self):
        random_word = uuid.uuid4().hex
        dirty_line = f"+\t{random_word}   \n"
        stream = io.StringIO(dirty_line)

        cleaned = self.sanitizer.strip_whitespace(stream)
        self.assertTrue(cleaned.startswith("+"))
        self.assertFalse(cleaned.endswith("   \n"))
        self.assertIn(random_word, cleaned)

    def test_remove_unsupported_binary_headers(self):
        binary_marker = uuid.uuid4().hex
        content = f"Binary files a/{binary_marker}.png and b/{binary_marker}.png differ\n+{uuid.uuid4().hex}"
        stream = io.StringIO(content)

        result = self.sanitizer.remove_binary_diffs(stream)
        self.assertNotIn(binary_marker, result)

    def test_sanitize_empty_stream_raises_error(self):
        stream = io.StringIO("")
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_large_patch_truncation_or_handling(self):
        lines = [f"+{uuid.uuid4().hex}" for _ in range(50)]
        content = "\n".join(lines)
        stream = io.StringIO(content)

        result = self.sanitizer.sanitize(stream)
        for line in lines:
            self.assertIn(line, result)


if __name__ == '__main__':
    unittest.main()