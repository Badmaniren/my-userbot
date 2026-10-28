import unittest
import io
import uuid
import random
import string
from unittest.mock import patch

from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError, sanitize_patch


class TestPatchSanitizerInquisition(unittest.TestCase):
    """Инквизиторский набор тестов для модуля patch_sanitizer."""

    def setUp(self):
        self.sanitizer = PatchSanitizer()
        self.random_prefix = uuid.uuid4().hex[:8]

    def test_sanitize_success_and_normalization(self):
        token_a = uuid.uuid4().hex
        token_b = uuid.uuid4().hex
        raw_content = f"index {token_a}..{token_b} 100644\r\n--- a/{token_a}\r\n+++ b/{token_b}\r\n@@ -1,3 +1,3 @@\r\n-line with trailing spaces   \r\n+new line here\r\n \r\n\r"
        
        stream = io.StringIO(raw_content)
        result = self.sanitizer.sanitize(stream)

        self.assertNotIn("\r", result)
        self.assertIn(token_a, result)
        self.assertIn(token_b, result)
        self.assertNotIn("   \n", result)

    def test_sanitize_empty_stream_raises_error(self):
        empty_stream = io.StringIO("")
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(empty_stream)

    def test_sanitize_null_bytes_raises_error(self):
        garbage = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\x00\nindex 1234..5678"
        stream = io.StringIO(garbage)
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_remove_binary_diffs(self):
        id1 = uuid.uuid4().hex
        id2 = uuid.uuid4().hex
        id3 = uuid.uuid4().hex
        raw = f"Binary files a/{id1} and b/{id2} differ\nindex {id3}..{id3} 100644\n--- a/{id3}\n+++ b/{id3}\n"
        stream = io.StringIO(raw)
        cleaned = self.sanitizer.remove_binary_diffs(stream)
        
        self.assertNotIn(id1, cleaned)
        self.assertNotIn(id2, cleaned)
        self.assertIn(id3, cleaned)

    def test_normalize_endings(self):
        rand_word = uuid.uuid4().hex
        crlf_content = f"{rand_word}\r\nsubtext\r\nother\r"
        stream = io.StringIO(crlf_content)
        normalized = self.sanitizer.normalize_endings(stream)
        
        self.assertNotIn("\r\n", normalized)
        self.assertNotIn("\r", normalized.replace("\n", ""))
        self.assertIn(rand_word, normalized)

    def test_strip_whitespace(self):
        val = uuid.uuid4().hex
        content = f"   {val}   \r\n"
        stream = io.StringIO(content)
        stripped = self.sanitizer.strip_whitespace(stream)
        
        self.assertTrue(stripped.endswith("\n"))
        self.assertIn(val, stripped)

    def test_sanitize_patch_wrapper(self):
        unique_token = uuid.uuid4().hex
        patch_text = f"diff --git a/{unique_token} b/{unique_token}\n--- a/{unique_token}\n+++ b/{unique_token}\n@@ -1 +1 @@\n-{unique_token}\n+{unique_token} modified   \n"
        res = sanitize_patch(patch_text)
        self.assertIn(unique_token, res)
        self.assertNotIn("   \n", res)


if __name__ == "__main__":
    unittest.main()