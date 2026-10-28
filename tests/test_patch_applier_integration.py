import unittest
import uuid
import random
import tempfile
import os
from pathlib import Path

from skills.patch_applier import patch_applier
from skills.code_sanitizer import CodeSanitizerError
from skills.patch_sanitizer import PatchSanitizerError


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.unique_id = str(uuid.uuid4())
        self.target_file_name = f"target_{self.unique_id}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        # Создаем базовый файл для применения патча
        self.initial_content = f"# Initial content {self.unique_id}\n\ndef foo():\n    return {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_apply_valid_patch_integration(self):
        random_return_value = random.randint(101, 1000)
        patch_content = f"""--- {self.target_file_name}
+++ {self.target_file_name}
@@ -3,2 +3,2 @@
 def foo():
-    return
+    return {random_return_value}
"""

        # Интеграционный вызов модуля без моков
        result = patch_applier.apply_patch(self.repo_path, patch_content)

        # Проверяем реальные изменения в файловой системе
        self.assertTrue(result, "Патч должен успешно примениться")

        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(str(random_return_value), updated_content, "Файл должен содержать изменения из патча")

    def test_apply_malformed_patch_integration(self):
        malformed_patch = f"INVALID PATCH DATA {uuid.uuid4()}"

        with self.assertRaises(Exception):
            patch_applier.apply_patch(self.repo_path, malformed_patch)

        # Убедимся, что файл не был поврежден при ошибке
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        self.assertEqual(current_content, self.initial_content, "Файл не должен измениться при неудачном патче")


if __name__ == "__main__":
    unittest.main()