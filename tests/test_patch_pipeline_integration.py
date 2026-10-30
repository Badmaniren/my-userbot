import unittest
import os
import uuid
import tempfile
import shutil
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier
from skills.patch_pipeline import run_patch_pipeline

class TestPatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path)

        self.target_file = os.path.join(self.repo_path, f"test_{uuid.uuid4().hex}.txt")
        with open(self.target_file, "w") as f:
            f.write("initial content\n")

        self.patch_id = uuid.uuid4().hex
        self.raw_patch = f"--- a/test.txt\n+++ b/test.txt\n@@ -1 +1 @@\n-initial content\n+patched content {self.patch_id}"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_full_cycle(self):
        # Проверка интеграции: Санитизация -> Проверка -> Применение
        # Без использования моков, работаем с реальными объектами

        result = run_patch_pipeline(
            raw_patch=self.raw_patch,
            repo_path=self.repo_path,
            target_file=self.target_file
        )

        # Проверка успешности конвейера
        self.assertTrue(result, "Pipeline failed to process the patch")

        # Проверка целостности: чтение файла после применения
        with open(self.target_file, "r") as f:
            content = f.read()

        self.assertIn(self.patch_id, content, "Patch content was not correctly applied to the file")
        self.assertEqual(content.strip(), f"patched content {self.patch_id}")

    def test_pipeline_invalid_patch_rejection(self):
        # Генерация мусорного патча для проверки устойчивости конвейера
        invalid_patch = f"INVALID_DATA_{uuid.uuid4().hex}"

        with self.assertRaises(Exception):
            run_patch_pipeline(
                raw_patch=invalid_patch,
                repo_path=self.repo_path,
                target_file=self.target_file
            )

        # Проверка, что файл не был поврежден при ошибке
        with open(self.target_file, "r") as f:
            self.assertEqual(f.read().strip(), "initial content")

if __name__ == "__main__":
    unittest.main()