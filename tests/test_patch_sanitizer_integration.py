import unittest
import io
import uuid
import random
from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError, sanitize_patch


class TestPatchSanitizerIntegration(unittest.TestCase):

    def test_patch_sanitizer_integration_flow(self):
        random_id = str(uuid.uuid4())
        trailing_spaces_count = random.randint(1, 5)
        
        raw_patch = (
            f"diff --git a/module_{random_id}.py b/module_{random_id}.py\n"
            f"--- a/module_{random_id}.py\n"
            f"+++ b/module_{random_id}.py\n"
            f"@@ -1,3 +1,3 @@\n"
            f"-def old_func():\r\n"
            f"+    def new_func():{' ' * trailing_spaces_count}\n"
            f" Binary files a/binary.bin and b/binary.bin differ \n"
        )

        sanitizer = PatchSanitizer()
        stream = io.StringIO(raw_patch)
        
        normalized_endings = sanitizer.normalize_endings(stream)
        self.assertNotIn("\r\n", normalized_endings)
        self.assertNotIn("\r", normalized_endings)

        stream_cleaned = io.StringIO(raw_patch)
        filtered_diffs = sanitizer.remove_binary_diffs(stream_cleaned)
        
        result_via_wrapper = sanitize_patch(raw_patch)
        
        self.assertIn(random_id, result_via_wrapper)
        self.assertIn("def new_func():", result_via_wrapper)
        
        lines = result_via_wrapper.splitlines()
        for line in lines:
            if line:
                self.assertFalse(line.endswith(" "))

    def test_patch_sanitizer_errors(self):
        sanitizer = PatchSanitizer()

        with self.assertRaises(PatchSanitizerError):
            sanitizer.sanitize(io.StringIO(""))

        null_byte_patch = f"diff --git a/file.py b/file.py\n\x00content_{uuid.uuid4()}"
        with self.assertRaises(PatchSanitizerError):
            sanitizer.sanitize(io.StringIO(null_byte_patch))


if __name__ == "__main__":
    unittest.main()