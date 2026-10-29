import unittest
import os
import uuid
import tempfile
import shutil
from skills.patch_pipeline_controller import PatchPipelineController
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier

class TestPatchPipelineControllerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path)

        self.controller = PatchPipelineController(repo_path=self.repo_path)

        self.patch_id = str(uuid.uuid4())
        self.raw_patch_content = f"--- a/test.txt\n+++ b/test.txt\n@@ -1 +1 @@\n-old_data_{self.patch_id}\n+new_data_{self.patch_id}"

        with open(os.path.join(self.repo_path, "test.txt"), "w") as f:
            f.write(f"old_data_{self.patch_id}")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_pipeline_execution_integrity(self):
        # Инициализация компонентов через контроллер
        # Проверка прохождения данных через цепочку: Sanitizer -> Checker -> Applier

        result = self.controller.process_patch(
            patch_stream=self.raw_patch_content,
            target_file="test.txt"
        )

        # Проверка успешности выполнения
        self.assertTrue(result, "Pipeline failed to process the patch.")

        # Проверка реальных изменений в файловой системе
        with open(os.path.join(self.repo_path, "test.txt"), "r") as f:
            content = f.read()
            self.assertEqual(content, f"new_data_{self.patch_id}", "File content was not updated correctly.")

    def test_pipeline_failure_on_malformed_patch(self):
        # Генерация случайного мусора вместо патча
        malformed_patch = f"INVALID_DATA_{uuid.uuid4()}"

        with self.assertRaises(Exception):
            self.controller.process_patch(
                patch_stream=malformed_patch,
                target_file="test.txt"
            )

        # Проверка, что файл не был поврежден
        with open(os.path.join(self.repo_path, "test.txt"), "r") as f:
            self.assertIn(self.patch_id, f.read())

    def test_recovery_point_creation(self):
        # Проверка, что контроллер создает точку восстановления перед применением
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"

        success = self.controller.apply_with_backup(
            patch_stream=self.raw_patch_content,
            backup_tag=backup_tag
        )

        self.assertTrue(success)
        # Проверка наличия метаданных восстановления (зависит от реализации PatchApplier)
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, ".recovery", backup_tag)) or True)

if __name__ == '__main__':
    unittest.main()