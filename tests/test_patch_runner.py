import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.patch_runner import PatchRunner

class TestPatchRunner(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.runner = PatchRunner(self.repo_path)

    def test_run_pipeline_success(self):
        # Генерируем случайные данные для пайплайна
        raw_patch = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n{uuid.uuid4().hex}"
        sanitized_patch = f"CLEAN_{uuid.uuid4().hex}"

        # Мокируем зависимости
        with patch('skills.patch_runner.PatchSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_runner.PatchVerifier') as mock_verifier_cls, \
             patch('skills.patch_runner.PatchApplier') as mock_applier_cls:

            # Настройка поведения моков
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = sanitized_patch

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            mock_applier = mock_applier_cls.return_value
            mock_applier.safe_apply.return_value = True

            # Запуск
            runner = PatchRunner(self.repo_path)
            result = runner.run_pipeline(raw_patch)

            # Проверки
            self.assertTrue(result)
            mock_sanitizer.sanitize.assert_called_once_with(raw_patch)
            mock_verifier.verify.assert_called_once_with(sanitized_patch)
            mock_applier.safe_apply.assert_called_once()

    def test_run_pipeline_sanitization_failure(self):
        raw_patch = uuid.uuid4().hex

        with patch('skills.patch_runner.PatchSanitizer') as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            # Имитируем ошибку санитизации
            mock_sanitizer.sanitize.side_effect = Exception(f"Sanitize error {uuid.uuid4().hex}")

            runner = PatchRunner(self.repo_path)
            with self.assertRaises(Exception):
                runner.run_pipeline(raw_patch)

    def test_run_pipeline_verification_failure(self):
        raw_patch = uuid.uuid4().hex
        sanitized_patch = uuid.uuid4().hex

        with patch('skills.patch_runner.PatchSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_runner.PatchVerifier') as mock_verifier_cls:

            mock_sanitizer_cls.return_value.sanitize.return_value = sanitized_patch
            mock_verifier = mock_verifier_cls.return_value
            # Верификация провалена
            mock_verifier.verify.return_value = False

            runner = PatchRunner(self.repo_path)
            result = runner.run_pipeline(raw_patch)

            self.assertFalse(result)

    def test_run_pipeline_applier_exception(self):
        raw_patch = uuid.uuid4().hex
        sanitized_patch = uuid.uuid4().hex
        backup_tag = uuid.uuid4().hex

        with patch('skills.patch_runner.PatchSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_runner.PatchVerifier') as mock_verifier_cls, \
             patch('skills.patch_runner.PatchApplier') as mock_applier_cls:

            mock_sanitizer_cls.return_value.sanitize.return_value = sanitized_patch
            mock_verifier_cls.return_value.verify.return_value = True

            mock_applier = mock_applier_cls.return_value
            # Имитируем падение при применении
            mock_applier.safe_apply.side_effect = Exception("Applier crash")

            runner = PatchRunner(self.repo_path)
            with self.assertRaises(Exception):
                runner.run_pipeline(raw_patch)

    def test_integration_flow_data_integrity(self):
        # Проверка передачи данных между этапами
        input_data = uuid.uuid4().hex
        expected_sanitized = f"proc_{input_data}"

        with patch('skills.patch_runner.PatchSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_runner.PatchVerifier') as mock_verifier_cls, \
             patch('skills.patch_runner.PatchApplier') as mock_applier_cls:

            mock_sanitizer_cls.return_value.sanitize.return_value = expected_sanitized

            runner = PatchRunner(self.repo_path)
            runner.run_pipeline(input_data)

            # Убеждаемся, что верификатор получил именно то, что вернул санитизатор
            mock_verifier_cls.return_value.verify.assert_called_with(expected_sanitized)

if __name__ == '__main__':
    unittest.main()