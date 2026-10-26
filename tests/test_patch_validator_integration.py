import unittest
import os
import uuid
import random
import shutil
import tempfile

from skills.patch_validator import PatchValidator
from skills.git_inspector import GitInspector
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestPatchValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        self.log_path = os.path.join(self.test_dir, "audit.log")
        os.makedirs(self.repo_path)

        # Инициализация реальных зависимых компонентов
        self.inspector = GitInspector(repo_path=self.repo_path)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=0.8
        )
        self.logger = AnomalyLogger(log_path=self.log_path)

        # Инициализация тестируемого модуля
        self.validator = PatchValidator(
            inspector=self.inspector,
            audit_hub=self.audit_hub,
            logger=self.logger
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_validation_lifecycle(self):
        # Генерация случайных данных для теста
        patch_id = str(uuid.uuid4())
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH"])
        random_payload = f"def test_func(): return {random.randint(100, 999)}"

        # 1. Формируем тестовый контекст (имитация изменений в репозитории)
        target_file = os.path.join(self.repo_path, f"patch_{patch_id}.py")
        with open(target_file, "w") as f:
            f.write(random_payload)

        # 2. Вызов метода валидации
        # Проверяем, что валидатор корректно взаимодействует с инспектором и аудитором
        result = self.validator.validate(
            patch_id=patch_id,
            file_path=target_file,
            severity=random_severity
        )

        # 3. Проверка результата
        self.assertTrue(result, "Валидатор должен вернуть True для корректного файла")

        # 4. Проверка интеграции с логгером (проверка записи в реальный файл)
        logs = self.logger.get_anomalies()
        self.assertGreater(len(logs), 0, "Логгер должен содержать записи после валидации")

        # 5. Проверка интеграции с аудитором (проверка агрегации метрик)
        report = self.audit_hub.generate_final_report()
        self.assertIn(patch_id, str(report), "ID патча должен присутствовать в отчете аудитора")

    def test_invalid_patch_rejection(self):
        # Генерация некорректного патча
        bad_patch_id = str(uuid.uuid4())
        bad_file = os.path.join(self.repo_path, "malicious.py")
        with open(bad_file, "w") as f:
            f.write("import os; os.system('rm -rf /')")

        # Валидация должна выявить аномалию
        result = self.validator.validate(
            patch_id=bad_patch_id,
            file_path=bad_file,
            severity="CRITICAL"
        )

        # Проверяем, что система отклонила патч
        self.assertFalse(result, "Валидатор должен отклонить опасный код")

        # Проверяем, что аномалия была зафиксирована в AuditHub
        anomalies = self.logger.get_anomalies()
        found = any(bad_patch_id in str(a) for a in anomalies)
        self.assertTrue(found, "Аномалия должна быть зафиксирована в системе аудита")

if __name__ == "__main__":
    unittest.main()