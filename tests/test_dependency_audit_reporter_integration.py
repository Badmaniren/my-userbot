import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.dependency_audit_reporter import generate_audit_report
from skills import dependency_audit_aggregator
from skills.repo_reporter import RepoReporter


class TestDependencyAuditReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Генерируем случайные данные для теста, исключая хардкод
        self.unique_id = str(uuid.uuid4())
        self.cve_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.report_filename = f"audit_report_{self.unique_id}.md"
        self.output_path = os.path.join(self.repo_path, self.report_filename)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dependency_audit_reporter_composition(self):
        # Проверяем, что модуль реально использует зависимости и создает файл отчета
        result_path = generate_audit_report(
            repo_path=self.repo_path,
            output_report_name=self.report_filename,
            cve_identifier=self.cve_id,
            target_version=self.target_version
        )

        # Проверяем, что функция возвращает путь к созданному файлу
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path), f"Файл отчета не был создан по пути: {result_path}")

        # Читаем содержимое файла и проверяем наличие уникальных сгенерированных данных
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(self.cve_id, content, "Сгенерированный CVE ID отсутствует в итоговом отчете")
        self.assertIn(self.target_version, content, "Целевая версия зависимости отсутствует в итоговом отчете")
        self.assertIn(self.unique_id, content, "Уникальный идентификатор теста отсутствует в отчете")

        # Дополнительно проверяем работу базового класса RepoReporter напрямую через интеграцию
        reporter = RepoReporter(repo_path=self.repo_path)
        final_report = reporter.generate_final_report()
        self.assertIsInstance(final_report, str)
        self.assertTrue(len(final_report) > 0)


if __name__ == '__main__':
    unittest.main()