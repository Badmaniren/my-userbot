import unittest
import uuid
import random
import os
import tempfile
import shutil
from skills.patch_validator import PatchValidator
from skills.code_sanitizer import CodeSanitizer
from skills.patch_sanitizer import PatchSanitizer
from skills.anomaly_logger import AnomalyLogger

class TestPatchValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, "anomaly.log")
        self.logger = AnomalyLogger(self.log_path)
        self.validator = PatchValidator()
        self.sanitizer = CodeSanitizer()
        self.patch_sanitizer = PatchSanitizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_patch_validation_lifecycle(self):
        # Генерируем случайные данные для теста
        patch_id = str(uuid.uuid4())
        random_code = f"def func_{random.randint(1000, 9999)}(): return {random.randint(0, 100)}"

        # 1. Санитизация кода
        sanitized_code = self.sanitizer.sanitize(random_code)

        # 2. Санитизация патча
        patch_data = {"id": patch_id, "content": sanitized_code}
        sanitized_patch = self.patch_sanitizer.sanitize(patch_data)

        # 3. Валидация через PatchValidator (Интеграционный этап)
        # Проверяем, что валидатор принимает данные, прошедшие через цепочку
        is_valid = self.validator.validate(sanitized_patch)

        self.assertTrue(is_valid, f"Patch {patch_id} should be valid after sanitization")

        # 4. Проверка логирования аномалий при попытке валидации некорректного патча
        malicious_patch = {"id": str(uuid.uuid4()), "content": "import os; os.system('rm -rf /')"}

        try:
            self.validator.validate(malicious_patch)
        except Exception:
            self.logger.log_anomaly(
                source="patch_validator",
                severity="CRITICAL",
                details=f"Detected malicious patch {malicious_patch['id']}",
                telemetry_snapshot={"random_seed": random.random()}
            )

        # Проверяем, что лог был создан и содержит наш ID
        logs = self.logger.get_anomalies()
        self.assertTrue(any(malicious_patch['id'] in str(log) for log in logs), "Anomaly not logged for malicious patch")

    def test_structural_integrity_with_random_payloads(self):
        # Проверка на случайных данных
        for _ in range(3):
            payload = {
                "id": str(uuid.uuid4()),
                "complexity": random.uniform(0, 1),
                "payload": f"data_{random.getrandbits(32)}"
            }

            # Валидатор должен корректно обрабатывать структуру
            result = self.validator.validate(payload)
            self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()