import unittest
import tempfile
import os
import shutil
import uuid
import random

from skills.patch_applier import apply_patch

class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file_name = f"test_file_{uuid.uuid4().hex}.py"
        self.file_path = os.path.join(self.test_dir, self.file_name)

        self.initial_comment = f"# Initial content {uuid.uuid4()}"
        self.original_content = f"{self.initial_comment}\nprint('hello')\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.original_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_applier_integration_flow(self):
        unique_string = f"print('patched_{uuid.uuid4().hex}')"
        patch_content = f"""--- {self.file_name}
+++ {self.file_name}
@@ -1,2 +1,2 @@
-{self.initial_comment}
+# Initial content modified
-print('hello')
+{unique_string}
"""
        # Проверяем работу dry-run (предварительной проверки)
        dry_run_result = apply_patch(self.file_path, patch_content, dry_run=True)

        with open(self.file_path, "r", encoding="utf-8") as f:
            content_after_dry = f.read()

        self.assertEqual(content_after_dry, self.original_content, "Dry-run не должен изменять исходный файл")

        # Применяем патч реально с созданием бэкапа
        success = apply_patch(self.file_path, patch_content, dry_run=False, backup=True)

        self.assertTrue(success, "Патч должен успешно примениться")

        with open(self.file_path, "r", encoding="utf-8") as f:
            final_content = f.read()

        self.assertIn(unique_string, final_content, "Файл должен содержать изменения из патча")

    def test_patch_applier_rollback_on_failure(self):
        invalid_patch = f"""--- {self.file_name}
+++ {self.file_name}
@@ -999,3 +999,3 @@
- nonexistent line
+ broken patch data {uuid.uuid4()}
"""
        # Попытка применить невалидный патч должна вызвать откат (rollback)
        success = apply_patch(self.file_path, invalid_patch, dry_run=False, backup=True)

        self.assertFalse(success, "Применение невалидного патча должно завершиться неудачей")

        with open(self.file_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        self.assertEqual(
            current_content,
            self.original_content,
            "Файл должен быть откатан до исходного состояния при сбое патча"
        )

if __name__ == "__main__":
    unittest.main()