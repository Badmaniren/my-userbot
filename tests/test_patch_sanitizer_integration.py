import unittest
import io
import uuid
import random
from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError, sanitize_patch


class TestPatchSanitizerIntegration(unittest.TestCase):

    def setUp(self):
        self.sanitizer = PatchSanitizer()

    def test_integration_pipeline_success(self):
        rand_id = str(uuid.uuid4())
        random_suffix = f"data_{random.randint(1000, 9999)}"

        raw_patch = (
            f"diff --git a/file_{rand_id}.py b/file_{rand_id}.py\r\n"
            f"index 1234567..89abcdef 100644\r\n"
            f"--- a/file_{rand_id}.py\r\n"
            f"+++ b/file_{rand_id}.py\r\n"
            f"@@ -1,3 +1,3 @@\r\n"
            f"-def old_func():   \r\n"
            f"+    # {random_suffix}\r\n"
            f"     Binary files a/bin_file and b/bin_file differ\r\n"
        )

        cleaned = sanitize_patch(raw_patch)

        self.assertNotIn("\r", cleaned)
        self.assertNotIn("Binary files", cleaned)
        self.assertIn(random_suffix, cleaned)
        self.assertTrue(all(not line.endswith(" ") for line in cleaned.splitlines()))

    def test_integration_empty_stream_raises(self):
        stream = io.StringIO("")
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)

    def test_integration_null_bytes_raises(self):
        rand_str = f"content_{uuid.uuid4()}\x00binary"
        stream = io.StringIO(rand_str)
        with self.assertRaises(PatchSanitizerError):
            self.sanitizer.sanitize(stream)


if __name__ == "__main__":
    unittest.main()