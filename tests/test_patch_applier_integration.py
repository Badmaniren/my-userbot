import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_applier import patch_applier
from skills.code_sanitizer import code_sanitizer
from skills.code_validator import code_validator

class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file_name = f"target_{uuid.uuid4().hex}.py"
        self.file_path = os.path.join(self.test_dir, self.file_name)

        self.random_id = random.randint(1000, 9999)
        self.initial_content = f"def get_value():\n    return {self.random_id}\n"

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_sanitized_patch_integration(self):
        new_random_id = random.randint(10000, 99999)
        raw_patch = f"def get_value():\n    return {new_random_id}\n"

        sanitized_code = code_sanitizer.sanitize(raw_patch)
        code_validator.validate(sanitized_code)

        result = patch_applier.apply_patch(self.file_path, sanitized_code)

        self.assertTrue(result, "Патч должен успешно примениться")

        with open(self.file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(str(new_random_id), updated_content)
        self.assertNotIn(str(self.random_id), updated_content)

if __name__ == "__main__":
    unittest.main()