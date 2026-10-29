import unittest
import os
import uuid
import shutil
import tempfile
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_verifier import PatchVerifier
from skills.patch_applier import PatchApplier
from skills.patch_runner import run_patch_pipeline

class TestPatchRunnerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path)

        self.patch_id = str(uuid.uuid4())
        self.raw_patch = f"--- a/test.txt\n+++ b/test.txt\n@@ -1 +1 @@\n-old_data\n+new_data_{self.patch_id}"

        self.sanitizer = PatchSanitizer()
        self.applier = PatchApplier(self.repo_path)
        self.verifier = PatchVerifier(self.repo_path, None, None, None, self.applier)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_patch_pipeline_integration(self):
        # 1. Санитизация
        sanitized_patch = self.sanitizer.sanitize(self.raw_patch)
        self.assertIn(self.patch_id, sanitized_patch, "Sanitizer corrupted the patch content")

        # 2. Верификация
        is_valid = self.verifier.verify_patch(sanitized_patch)
        self.assertTrue(is_valid, "Verifier rejected a valid patch")

        # 3. Применение через runner (интеграционный вызов)
        # runner должен использовать импортированные компоненты для сквозного процесса
        success = run_patch_pipeline(self.repo_path, sanitized_patch)

        self.assertTrue(success, "Pipeline failed to apply the patch")

        # 4. Проверка реального состояния
        # Проверяем, что состояние репозитория изменилось согласно патчу
        repo_state = self.applier.verify_repository_state()
        self.assertTrue(repo_state, "Repository state verification failed after application")

    def test_pipeline_rollback_on_failure(self):
        invalid_patch = "INVALID_PATCH_CONTENT_FOR_TESTING"

        # Проверка, что пайплайн корректно обрабатывает ошибки без падения системы
        try:
            result = run_patch_pipeline(self.repo_path, invalid_patch)
            self.assertFalse(result, "Pipeline should return False for invalid patches")
        except Exception as e:
            self.fail(f"Pipeline raised unexpected exception: {e}")

if __name__ == '__main__':
    unittest.main()