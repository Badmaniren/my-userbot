import unittest
import os
import shutil
import uuid
import tempfile
from skills.repo_security_pipeline import RepoSecurityPipeline
from skills.repo_security_gateway import RepoSecurityGateway
from skills.vulnerability_analyzer import VulnerabilityAnalyzer

class TestRepoSecurityPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, str(uuid.uuid4()))
        os.makedirs(self.repo_path)

        # Инициализация реальных объектов без моков
        self.gateway = RepoSecurityGateway(self.repo_path)
        self.analyzer = VulnerabilityAnalyzer(self.repo_path)
        self.pipeline = RepoSecurityPipeline(self.repo_path)

        self.run_id = str(uuid.uuid4())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_security_pipeline_integration_flow(self):
        # Генерируем случайный файл с "уязвимостью" для теста
        vuln_file = os.path.join(self.repo_path, f"requirements_{self.run_id}.txt")
        with open(vuln_file, "w") as f:
            f.write("insecure-package==0.0.1")

        # 1. Запуск анализатора для оценки рисков
        analysis_result = self.analyzer.run()
        self.assertIsInstance(analysis_result, dict, "Анализатор должен вернуть отчет в виде словаря")

        # 2. Запуск шлюза безопасности
        gateway_result = self.gateway.scan_and_evaluate()
        self.assertIn('status', gateway_result, "Шлюз должен вернуть статус проверки")

        # 3. Интеграционный вызов пайплайна
        # Ожидаем, что пайплайн скомпонует работу шлюза и анализатора
        pipeline_status = self.pipeline.execute_security_check()

        # Проверка: если пайплайн обнаружил критическую угрозу, он должен вернуть False (прерывание)
        # или соответствующий статус код
        self.assertFalse(pipeline_status, "Пайплайн должен прервать выполнение при наличии уязвимостей")

        # Проверка побочных эффектов: создание лога или отчета
        report_path = os.path.join(self.repo_path, f"security_report_{self.run_id}.json")
        self.analyzer.build_security_report({"id": self.run_id, "status": "critical"}, report_path)

        self.assertTrue(os.path.exists(report_path), "Файл отчета должен быть создан в репозитории")

        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn(self.run_id, content, "Отчет должен содержать уникальный ID текущей сессии")

    def test_pipeline_success_path(self):
        # Тест на чистом репозитории
        clean_path = os.path.join(self.test_dir, str(uuid.uuid4()))
        os.makedirs(clean_path)

        pipeline = RepoSecurityPipeline(clean_path)
        result = pipeline.execute_security_check()

        # Если угроз нет, пайплайн должен завершиться успешно (True)
        self.assertTrue(result, "Пайплайн должен успешно завершиться при отсутствии угроз")

if __name__ == '__main__':
    unittest.main()