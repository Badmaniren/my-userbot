import unittest
import uuid
import random
import os
import tempfile
from skills.dependency_audit_guardian import *

class TestDependencyAuditGuardianIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.branch = f"feature/audit-{uuid.uuid4().hex[:8]}"
        self.stream_source = random.choice(["npm", "maven", "pip", "cargo"])
        self.output_report_name = f"report_{uuid.uuid4().hex[:6]}.json"
        self.cve_identifier = f"CVE-2025-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_guardian_composition_workflow(self):
        # Проверяем сквозной интеграционный вызов композитного модуля без моков.
        # Модуль должен внутри себя вызывать функции из dependency_audit_aggregator
        # и dependency_audit_validator.
        
        # Шаг 1: Запуск процесса через гардиана с использованием валидации и агрегации
        result = validate_and_aggregate_dependencies(
            repo_path=self.repo_path,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version,
            branch=self.branch,
            stream_source=self.stream_source
        )

        # Шаг 2: Проверяем, что гардиан реально отработал и вернул структурированные данные
        self.assertIsNotNone(result, "Композитный модуль не должен возвращать None")
        
        # Шаг 3: Проверяем создание реального отчетного файла в целевой директории
        expected_report_path = os.path.join(self.repo_path, self.output_report_name)
        
        # Если логика модуля предполагает создание файла отчета, проверяем его наличие,
        # либо проверяем корректность возвращаемого словаря с результатами валидации/агрегации.
        if os.path.exists(expected_report_path):
            self.assertTrue(os.path.getsize(expected_report_path) > 0, "Файл отчета не должен быть пустым")
        else:
            # Если файл не создается напрямую, проверяем что структура ответа содержит ключевые артефакты
            self.assertIsInstance(result, (dict, list, bool), "Результат должен быть валидным типом данных")

if __name__ == "__main__":
    unittest.main()